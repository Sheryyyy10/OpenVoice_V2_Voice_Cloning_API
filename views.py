import os
import torch
from pydub import AudioSegment
from django.http import JsonResponse
from django.views import View
from django.conf import settings
from openvoice import se_extractor
from openvoice.api import ToneColorConverter
from melo.api import TTS
from rest_framework.views import APIView

# Setup paths
CKPT_CONVERTER = '/home/hellcat/PycharmProjects/OpenVoice_Voice_Cloning_API/checkpoints_v2/converter'
OUTPUT_DIR = '/home/hellcat/PycharmProjects/OpenVoice_Voice_Cloning_API/checkpoints_v2/outputs_v2'
os.makedirs(OUTPUT_DIR, exist_ok=True)

DEVICE = "cuda:0" if torch.cuda.is_available() else "cpu"
tone_color_converter = ToneColorConverter(f'{CKPT_CONVERTER}/config.json', device=DEVICE)
tone_color_converter.load_ckpt(f'{CKPT_CONVERTER}/checkpoint.pth')


class VoiceCloneView(APIView):
    def post(self, request):
        # Extract user input from request
        reference_speaker = request.FILES.get('reference_speaker')
        text = request.POST.get('text')
        speed = float(request.POST.get('speed', 1.0))  # Default speed is 0.8

        # Save the reference speaker file
        reference_speaker_path = os.path.join(settings.MEDIA_ROOT, 'Audio', reference_speaker.name)
        os.makedirs(os.path.dirname(reference_speaker_path), exist_ok=True)

        with open(reference_speaker_path, 'wb+') as f:
            for chunk in reference_speaker.chunks():
                f.write(chunk)

        # Extract speaker embeddings
        target_se, _ = se_extractor.get_se(reference_speaker_path, tone_color_converter, vad=False)

        # Initialize TTS model for English
        language = 'EN'
        model = TTS(language=language, device=DEVICE)
        speaker_ids = model.hps.data.spk2id

        src_path = os.path.join(settings.MEDIA_ROOT, 'Audio', 'tmp.wav')
        save_path = os.path.join(settings.MEDIA_ROOT, 'Audio', 'output_v2_en_default.wav')

        # Generate TTS audio file using the first speaker (default)
        speaker_id = list(speaker_ids.values())[0]
        source_se = torch.load('/home/hellcat/PycharmProjects/OpenVoice_Voice_Cloning_API/checkpoints_v2/base_speakers/ses/en-default.pth', map_location=DEVICE)

        model.tts_to_file(text, speaker_id, src_path, speed=speed)

        # Run the tone color converter
        encode_message = "@Funsol"
        tone_color_converter.convert(
            audio_src_path=src_path,
            src_se=source_se,
            tgt_se=target_se,
            output_path=save_path,
            message=encode_message
        )

        # Return the media URL to the generated voice file
        audio_url = request.build_absolute_uri(f'{settings.MEDIA_URL}Audio/output_v2_en_default.wav')
        return JsonResponse({'output_path': audio_url})
