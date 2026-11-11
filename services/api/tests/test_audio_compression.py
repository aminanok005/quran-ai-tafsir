import io
import shutil
import unittest
import wave

from services.api.services.translation_audio import compress_wav_to_mp3


def make_wav(seconds=1, rate=24000):
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(b"\x10\x20" * rate * seconds)
    return buffer.getvalue()


class CompressWavTests(unittest.IsolatedAsyncioTestCase):
    @unittest.skipUnless(shutil.which("ffmpeg"), "ffmpeg not installed")
    async def test_wav_becomes_smaller_mp3(self):
        wav = make_wav()
        result = await compress_wav_to_mp3(wav)
        self.assertLess(len(result), len(wav))
        self.assertTrue(result.startswith(b"ID3") or result[0] == 0xFF)

    async def test_invalid_audio_falls_back_to_original(self):
        garbage = b"RIFF\x00\x00\x00\x00WAVEnot-really-audio"
        self.assertEqual(await compress_wav_to_mp3(garbage), garbage)


if __name__ == "__main__":
    unittest.main()
