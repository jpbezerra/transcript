import yt_dlp
import youtube_transcript_api

class Transcriptor:
    def __init__(self, url):
        self.url = url
        self.video_id = self.extract_video_id()

    def extract_video_id(self):
        with yt_dlp.YoutubeDL() as ydl:
            info = ydl.extract_info(self.url, download=False)
            return info.get("id")
        
    def _get_text(self, snippet):
        if isinstance(snippet, dict):
            return snippet.get("text", "")
        return getattr(snippet, "text", "")
    
    def get_youtube_transcript(self, video_id, langs=None):
        """Obtém a transcrição (oficial/gerada) nas línguas preferidas."""
        langs = langs or ["pt", "pt-BR", "en"]
        api = youtube_transcript_api.YouTubeTranscriptApi()

        try:
            data = api.fetch(self.video_id, languages=langs)
            return " ".join(t for t in (self._get_text(s) for s in data) if t.strip())
        except youtube_transcript_api.NoTranscriptFound:
            pass
        except youtube_transcript_api.TranscriptsDisabled:
            return "Transcrições desabilitadas para este vídeo."
        except Exception as e:
            return f"Falha ao obter transcrição oficial: {e}"

        try:
            listing = api.list(video_id)

            for lang in langs:
                try:
                    t = listing.find_generated_transcript([lang])
                    data = t.fetch()
                    return " ".join(txt for txt in (self._get_text(s) for s in data) if txt.strip())
                except Exception:
                    continue

            for t in listing:
                try:
                    data = t.fetch()
                    out = " ".join(txt for txt in (self._get_text(s) for s in data) if txt.strip())
                    if out:
                        return out
                except Exception:
                    continue

            return "Nenhuma transcrição disponível para este vídeo."
        except youtube_transcript_api.TranscriptsDisabled:
            return "Transcrições desabilitadas para este vídeo."
        except Exception as e:
            return f"Falha ao listar transcrições: {e}"