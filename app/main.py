from .transcriptor import Transcriptor

def main():
    while True:
        url = input("Digite a URL do vídeo do YouTube (ou 'sair' para encerrar): ")
        if url.lower() == 'sair':
            break

        transcriptor = Transcriptor(url)
        video_id = transcriptor.video_id

        if not video_id:
            print("Não foi possível extrair o ID do vídeo. Verifique a URL e tente novamente.")
            continue
        
        transcript = transcriptor.get_youtube_transcript(video_id)
        print("Transcrição:")
        print(transcript)

if __name__ == "__main__":
    main()