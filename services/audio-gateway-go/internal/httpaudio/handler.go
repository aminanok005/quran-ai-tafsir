package httpaudio

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strconv"
	"strings"
	"time"
)

type Handler struct {
	Client      *http.Client
	BaseURL     string
	MaxRequests chan struct{}
	Timeout     time.Duration
	MaxBytes    int64
}

func New(baseURL string, concurrency int) *Handler {
	if concurrency < 1 {
		concurrency = 1
	}
	base := strings.TrimRight(baseURL, "/")
	client := &http.Client{}
	client.CheckRedirect = func(req *http.Request, via []*http.Request) error {
		if len(via) == 0 || req.URL.Host == via[0].URL.Host {
			return nil
		}
		return fmt.Errorf("redirect to unapproved host")
	}
	return &Handler{Client: client, BaseURL: base, MaxRequests: make(chan struct{}, concurrency), Timeout: 10 * time.Second, MaxBytes: 8 * 1024 * 1024}
}

func (h *Handler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		w.Header().Set("Allow", http.MethodGet)
		writeError(w, http.StatusMethodNotAllowed, "method_not_allowed")
		return
	}
	if r.URL.Path != "/audio" {
		writeError(w, http.StatusNotFound, "not_found")
		return
	}
	reciter, surah, ayah, audioNumber := r.URL.Query().Get("reciter"), r.URL.Query().Get("surah"), r.URL.Query().Get("ayah"), r.URL.Query().Get("audio_number")
	if reciter != "ar.alafasy" || !validSurah(surah) || !validAyah(ayah) || !validAudioNumber(audioNumber) {
		writeError(w, http.StatusBadRequest, "invalid_audio_request")
		return
	}
	u, err := url.Parse(h.BaseURL + "/" + reciter + "/" + audioNumber + ".mp3")
	if err != nil || u.Scheme != "http" && u.Scheme != "https" {
		writeError(w, http.StatusBadGateway, "invalid_upstream")
		return
	}
	ctx, cancel := context.WithTimeout(r.Context(), h.Timeout)
	defer cancel()
	select {
	case h.MaxRequests <- struct{}{}:
		defer func() { <-h.MaxRequests }()
	case <-ctx.Done():
		writeError(w, http.StatusGatewayTimeout, "audio_timeout")
		return
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, u.String(), nil)
	if err != nil {
		writeError(w, http.StatusBadGateway, "upstream_request")
		return
	}
	if v := r.Header.Get("Range"); v != "" {
		req.Header.Set("Range", v)
	}
	resp, err := h.Client.Do(req)
	if err != nil {
		if ctx.Err() != nil {
			writeError(w, http.StatusGatewayTimeout, "audio_timeout")
		} else {
			writeError(w, http.StatusBadGateway, "upstream_unavailable")
		}
		return
	}
	defer resp.Body.Close()
	if resp.StatusCode == http.StatusRequestedRangeNotSatisfiable {
		writeError(w, http.StatusRequestedRangeNotSatisfiable, "invalid_range")
		return
	}
	if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusPartialContent {
		writeError(w, http.StatusBadGateway, "upstream_unavailable")
		return
	}
	if !strings.HasPrefix(strings.ToLower(resp.Header.Get("Content-Type")), "audio/mpeg") {
		writeError(w, http.StatusBadGateway, "invalid_upstream_content_type")
		return
	}
	if h.MaxBytes > 0 && resp.ContentLength > h.MaxBytes {
		writeError(w, http.StatusBadGateway, "audio_too_large")
		return
	}
	w.Header().Set("Content-Type", resp.Header.Get("Content-Type"))
	w.Header().Set("Accept-Ranges", "bytes")
	if v := resp.Header.Get("Content-Length"); v != "" {
		w.Header().Set("Content-Length", v)
	}
	if v := resp.Header.Get("Content-Range"); v != "" {
		w.Header().Set("Content-Range", v)
	}
	for _, header := range []string{"ETag", "Last-Modified", "Cache-Control"} {
		if value := resp.Header.Get(header); value != "" {
			w.Header().Set(header, value)
		}
	}
	w.WriteHeader(resp.StatusCode)
	if h.MaxBytes > 0 {
		_, _ = io.Copy(w, io.LimitReader(resp.Body, h.MaxBytes))
		return
	}
	_, _ = io.Copy(w, resp.Body)
}

func writeError(w http.ResponseWriter, status int, code string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(map[string]any{"version": 1, "code": code, "message": "audio request failed"})
}

func validSurah(v string) bool {
	number, err := strconv.Atoi(v)
	return err == nil && number >= 1 && number <= 114
}

func validAyah(v string) bool {
	number, err := strconv.Atoi(v)
	return err == nil && number >= 1 && number <= 200
}

func validAudioNumber(v string) bool {
	number, err := strconv.Atoi(v)
	return err == nil && number >= 1 && number <= 6236
}
