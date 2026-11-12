package main

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestHealthHandler(t *testing.T) {
	request := httptest.NewRequest(http.MethodGet, "/health", nil)
	writer := httptest.NewRecorder()
	healthHandler(writer, request)
	if writer.Code != http.StatusOK || writer.Header().Get("Content-Type") != "application/json" || !strings.Contains(writer.Body.String(), `"status":"ok"`) {
		t.Fatalf("status=%d content-type=%q body=%q", writer.Code, writer.Header().Get("Content-Type"), writer.Body.String())
	}
}

func TestHealthHandlerRejectsNonGet(t *testing.T) {
	request := httptest.NewRequest(http.MethodPost, "/health", nil)
	writer := httptest.NewRecorder()
	healthHandler(writer, request)
	if writer.Code != http.StatusMethodNotAllowed || writer.Header().Get("Allow") != http.MethodGet {
		t.Fatalf("status=%d allow=%q", writer.Code, writer.Header().Get("Allow"))
	}
}

func TestValidProductionUpstream(t *testing.T) {
	if !validProductionUpstream("https://cdn.islamic.network/quran/audio/128") {
		t.Fatal("expected canonical CDN upstream to be accepted")
	}
	for _, rawURL := range []string{"http://cdn.islamic.network/quran/audio/128", "https://example.test/quran/audio/128", "https://cdn.islamic.network/other"} {
		if validProductionUpstream(rawURL) {
			t.Fatalf("accepted %q", rawURL)
		}
	}
}
