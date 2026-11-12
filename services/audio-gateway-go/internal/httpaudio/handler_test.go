package httpaudio

import (
	"context"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync/atomic"
	"testing"
	"time"
)

func TestHandlerStreamsAllowlistedAudioAndRange(t *testing.T) {
	var receivedRange string
	upstream := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		receivedRange = r.Header.Get("Range")
		w.Header().Set("Content-Type", "audio/mpeg")
		w.Header().Set("Content-Range", "bytes 0-2/3")
		w.Header().Set("ETag", `"audio-etag"`)
		w.Header().Set("Last-Modified", "Thu, 12 Nov 2026 00:00:00 GMT")
		w.Header().Set("Cache-Control", "max-age=60")
		w.WriteHeader(http.StatusPartialContent)
		_, _ = w.Write([]byte("abc"))
	}))
	defer upstream.Close()
	h := New(upstream.URL, 1)
	r := httptest.NewRequest(http.MethodGet, "/audio?reciter=ar.alafasy&surah=1&ayah=2&audio_number=2", nil)
	r.Header.Set("Range", "bytes=0-2")
	w := httptest.NewRecorder()
	h.ServeHTTP(w, r)
	if w.Code != http.StatusPartialContent || w.Body.String() != "abc" || w.Header().Get("Content-Range") == "" || w.Header().Get("ETag") != `"audio-etag"` || w.Header().Get("Last-Modified") == "" || w.Header().Get("Cache-Control") != "max-age=60" {
		t.Fatalf("unexpected response: %d %q %#v", w.Code, w.Body.String(), w.Header())
	}
	if receivedRange != "bytes=0-2" {
		t.Fatalf("upstream Range=%q", receivedRange)
	}
}

func TestHandlerRejectsUnallowlistedReciter(t *testing.T) {
	h := New("http://127.0.0.1", 1)
	w := httptest.NewRecorder()
	h.ServeHTTP(w, httptest.NewRequest(http.MethodGet, "/audio?reciter=other&surah=1&ayah=1&audio_number=1", nil))
	if w.Code != http.StatusBadRequest {
		t.Fatalf("status=%d", w.Code)
	}
}

func TestHandlerRejectsInvalidQuranCoordinates(t *testing.T) {
	handler := New("http://127.0.0.1", 1)
	for _, query := range []string{"surah=115&ayah=1", "surah=1&ayah=201"} {
		request := httptest.NewRequest(http.MethodGet, "/audio?reciter=ar.alafasy&audio_number=1&"+query, nil)
		writer := httptest.NewRecorder()
		handler.ServeHTTP(writer, request)
		if writer.Code != http.StatusBadRequest {
			t.Fatalf("query=%s status=%d", query, writer.Code)
		}
	}
}

func TestHandlerRejectsNonGetMethods(t *testing.T) {
	handler := New("http://127.0.0.1", 1)
	request := httptest.NewRequest(http.MethodPost, "/audio", nil)
	writer := httptest.NewRecorder()
	handler.ServeHTTP(writer, request)
	if writer.Code != http.StatusMethodNotAllowed || writer.Header().Get("Allow") != http.MethodGet || writer.Header().Get("Content-Type") != "application/json" || !strings.Contains(writer.Body.String(), `"version":1`) {
		t.Fatalf("status=%d allow=%q", writer.Code, writer.Header().Get("Allow"))
	}
}

func TestHandlerRejectsUnexpectedPaths(t *testing.T) {
	handler := New("http://127.0.0.1", 1)
	request := httptest.NewRequest(http.MethodGet, "/admin", nil)
	writer := httptest.NewRecorder()
	handler.ServeHTTP(writer, request)
	if writer.Code != http.StatusNotFound {
		t.Fatalf("status=%d", writer.Code)
	}
}

func TestHandlerRejectsRedirectToUnapprovedHost(t *testing.T) {
	target := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { _, _ = w.Write([]byte("secret")) }))
	defer target.Close()
	redirect := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { http.Redirect(w, r, target.URL, http.StatusFound) }))
	defer redirect.Close()
	handler := New(redirect.URL, 1)
	request := httptest.NewRequest(http.MethodGet, "/audio?reciter=ar.alafasy&surah=1&ayah=3&audio_number=3", nil)
	writer := httptest.NewRecorder()
	handler.ServeHTTP(writer, request)
	if writer.Code != http.StatusBadGateway {
		t.Fatalf("status=%d body=%q", writer.Code, writer.Body.String())
	}
}

func TestHandlerRejectsKnownOversizedResponse(t *testing.T) {
	upstream := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Length", "4")
		_, _ = w.Write([]byte("toolarge"))
	}))
	defer upstream.Close()
	handler := New(upstream.URL, 1)
	handler.MaxBytes = 3
	request := httptest.NewRequest(http.MethodGet, "/audio?reciter=ar.alafasy&surah=1&ayah=3&audio_number=3", nil)
	writer := httptest.NewRecorder()
	handler.ServeHTTP(writer, request)
	if writer.Code != http.StatusBadGateway {
		t.Fatalf("status=%d body=%q", writer.Code, writer.Body.String())
	}
}

func TestHandlerCapsUnknownLengthResponse(t *testing.T) {
	upstream := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "audio/mpeg")
		w.WriteHeader(http.StatusOK)
		if flusher, ok := w.(http.Flusher); ok {
			flusher.Flush()
		}
		_, _ = w.Write([]byte("123456"))
	}))
	defer upstream.Close()
	handler := New(upstream.URL, 1)
	handler.MaxBytes = 3
	request := httptest.NewRequest(http.MethodGet, "/audio?reciter=ar.alafasy&surah=1&ayah=3&audio_number=3", nil)
	writer := httptest.NewRecorder()
	handler.ServeHTTP(writer, request)
	if writer.Code != http.StatusOK || writer.Body.Len() != 3 {
		t.Fatalf("status=%d bytes=%d", writer.Code, writer.Body.Len())
	}
}

func TestHandlerReturnsSafeInvalidRangeError(t *testing.T) {
	upstream := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusRequestedRangeNotSatisfiable)
	}))
	defer upstream.Close()
	handler := New(upstream.URL, 1)
	request := httptest.NewRequest(http.MethodGet, "/audio?reciter=ar.alafasy&surah=1&ayah=3&audio_number=3", nil)
	request.Header.Set("Range", "bytes=999-1000")
	writer := httptest.NewRecorder()
	handler.ServeHTTP(writer, request)
	if writer.Code != http.StatusRequestedRangeNotSatisfiable || !strings.Contains(writer.Body.String(), "invalid_range") {
		t.Fatalf("status=%d body=%q", writer.Code, writer.Body.String())
	}
}

func TestHandlerRejectsNonAudioSuccessResponse(t *testing.T) {
	upstream := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/xml")
		_, _ = w.Write([]byte("not audio"))
	}))
	defer upstream.Close()
	handler := New(upstream.URL, 1)
	request := httptest.NewRequest(http.MethodGet, "/audio?reciter=ar.alafasy&surah=1&ayah=3&audio_number=3", nil)
	writer := httptest.NewRecorder()
	handler.ServeHTTP(writer, request)
	if writer.Code != http.StatusBadGateway || !strings.Contains(writer.Body.String(), "invalid_upstream_content_type") {
		t.Fatalf("status=%d body=%q", writer.Code, writer.Body.String())
	}
}

func TestHandlerTimesOutSlowUpstream(t *testing.T) {
	upstream := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		<-r.Context().Done()
	}))
	defer upstream.Close()
	handler := New(upstream.URL, 1)
	handler.Timeout = 10 * time.Millisecond
	request := httptest.NewRequest(http.MethodGet, "/audio?reciter=ar.alafasy&surah=1&ayah=3&audio_number=3", nil)
	writer := httptest.NewRecorder()
	handler.ServeHTTP(writer, request)
	if writer.Code != http.StatusGatewayTimeout {
		t.Fatalf("status=%d body=%q", writer.Code, writer.Body.String())
	}
}

func TestHandlerPropagatesClientCancellation(t *testing.T) {
	started := make(chan struct{})
	cancelled := make(chan struct{})
	upstream := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		close(started)
		<-r.Context().Done()
		close(cancelled)
	}))
	defer upstream.Close()
	handler := New(upstream.URL, 1)
	requestContext, cancel := context.WithCancel(context.Background())
	request := httptest.NewRequest(http.MethodGet, "/audio?reciter=ar.alafasy&surah=1&ayah=3&audio_number=3", nil).WithContext(requestContext)
	done := make(chan struct{})
	go func() { handler.ServeHTTP(httptest.NewRecorder(), request); close(done) }()
	<-started
	cancel()
	select {
	case <-cancelled:
	case <-time.After(time.Second):
		t.Fatal("upstream request was not cancelled")
	}
	<-done
}

func TestHandlerBoundsUpstreamConcurrency(t *testing.T) {
	var active, peak int32
	release := make(chan struct{})
	upstream := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		current := atomic.AddInt32(&active, 1)
		for {
			previous := atomic.LoadInt32(&peak)
			if current <= previous || atomic.CompareAndSwapInt32(&peak, previous, current) {
				break
			}
		}
		<-release
		atomic.AddInt32(&active, -1)
		_, _ = w.Write([]byte("ok"))
	}))
	defer upstream.Close()
	handler := New(upstream.URL, 1)
	request := func() {
		handler.ServeHTTP(httptest.NewRecorder(), httptest.NewRequest(http.MethodGet, "/audio?reciter=ar.alafasy&surah=1&ayah=3&audio_number=3", nil))
	}
	done := make(chan struct{}, 2)
	go func() { request(); done <- struct{}{} }()
	time.Sleep(20 * time.Millisecond)
	go func() { request(); done <- struct{}{} }()
	time.Sleep(20 * time.Millisecond)
	if atomic.LoadInt32(&peak) != 1 {
		t.Fatalf("peak concurrency=%d", atomic.LoadInt32(&peak))
	}
	close(release)
	<-done
	<-done
}

func BenchmarkNativeAudio(b *testing.B) {
	payload := make([]byte, 64*1024)
	upstream := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "audio/mpeg")
		_, _ = w.Write(payload)
	}))
	defer upstream.Close()
	client := upstream.Client()
	b.ReportAllocs()
	b.SetBytes(int64(len(payload)))
	for index := 0; index < b.N; index++ {
		response, err := client.Get(upstream.URL)
		if err != nil {
			b.Fatal(err)
		}
		if _, err := io.Copy(io.Discard, response.Body); err != nil {
			b.Fatal(err)
		}
		_ = response.Body.Close()
	}
}

func BenchmarkGatewayAudio(b *testing.B) {
	payload := make([]byte, 64*1024)
	upstream := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "audio/mpeg")
		_, _ = w.Write(payload)
	}))
	defer upstream.Close()
	handler := New(upstream.URL, 16)
	b.ReportAllocs()
	b.SetBytes(int64(len(payload)))
	for index := 0; index < b.N; index++ {
		request := httptest.NewRequest(http.MethodGet, "/audio?reciter=ar.alafasy&surah=1&ayah=3&audio_number=3", nil)
		writer := httptest.NewRecorder()
		handler.ServeHTTP(writer, request)
		if writer.Code != http.StatusOK || writer.Body.Len() != len(payload) {
			b.Fatalf("status=%d bytes=%d", writer.Code, writer.Body.Len())
		}
	}
}
