package main

import (
	"context"
	"encoding/json"
	"log"
	"net/http"
	"net/url"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"quran-intelligent-tafsir/audio-gateway/internal/httpaudio"
)

func main() {
	base := os.Getenv("AUDIO_UPSTREAM_BASE_URL")
	if !validProductionUpstream(base) {
		log.Fatal("AUDIO_UPSTREAM_BASE_URL must be https://cdn.islamic.network/quran/audio/128")
	}
	streamer := httpaudio.New(base, 8)
	mux := http.NewServeMux()
	mux.Handle("/audio", streamer)
	mux.HandleFunc("/health", healthHandler)
	server := &http.Server{
		Addr:              ":8090",
		Handler:           mux,
		ReadHeaderTimeout: 5 * time.Second,
		IdleTimeout:       30 * time.Second,
		WriteTimeout:      30 * time.Second,
	}
	shutdown := make(chan os.Signal, 1)
	signal.Notify(shutdown, os.Interrupt, syscall.SIGTERM)
	go func() {
		<-shutdown
		ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()
		_ = server.Shutdown(ctx)
	}()
	if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		log.Fatal(err)
	}
}

func validProductionUpstream(rawURL string) bool {
	parsed, err := url.Parse(rawURL)
	return err == nil && parsed.Scheme == "https" && parsed.Hostname() == "cdn.islamic.network" && strings.TrimRight(parsed.Path, "/") == "/quran/audio/128"
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		w.Header().Set("Allow", http.MethodGet)
		w.WriteHeader(http.StatusMethodNotAllowed)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(map[string]any{"status": "ok", "version": 1, "capabilities": []string{"audio_stream", "range"}})
}
