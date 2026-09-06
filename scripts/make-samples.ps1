# Generates test recordings in samples\ using Windows TTS (requires ru-RU and en-US voices).
# Samples are gitignored; run this script to recreate them.
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech

$dir = Join-Path (Split-Path $PSScriptRoot) 'samples'
New-Item -ItemType Directory -Force $dir | Out-Null
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer

function Save-Speech([string]$File, [System.Speech.Synthesis.PromptBuilder]$Prompt) {
    $s.SetOutputToWaveFile((Join-Path $dir $File))
    $s.Speak($Prompt)
    $s.SetOutputToNull()
    Write-Host "  $File"
}

Write-Host 'Generating samples:'

$pb = New-Object System.Speech.Synthesis.PromptBuilder
$pb.StartVoice('Microsoft Irina Desktop')
$pb.AppendText('Добрый день! Это короткая тестовая запись на русском языке. Проверяем, как модель распознаёт обычную речь.')
$pb.EndVoice()
Save-Speech 'ru_short.wav' $pb

$pb = New-Object System.Speech.Synthesis.PromptBuilder
$pb.StartVoice('Microsoft Zira Desktop')
$pb.AppendText('Good afternoon! This is a short test recording in English. We are checking how the model handles everyday speech.')
$pb.EndVoice()
Save-Speech 'en_short.wav' $pb

$pb = New-Object System.Speech.Synthesis.PromptBuilder
$pb.StartVoice('Microsoft Irina Desktop')
$pb.AppendText('Сегодня мы обсудим планы на следующий квартал. Главная цель — выпустить новую версию продукта до конца ноября.')
$pb.AppendBreak([TimeSpan]::FromSeconds(2.5))
$pb.AppendText('Второй вопрос касается команды. Нам нужно нанять двух разработчиков и одного дизайнера. Собеседования начнутся на следующей неделе.')
$pb.AppendBreak([TimeSpan]::FromSeconds(2.5))
$pb.AppendText('И последнее. Бюджет на маркетинг увеличен на двадцать процентов. Прошу подготовить предложения до пятницы.')
$pb.EndVoice()
Save-Speech 'ru_meeting.wav' $pb

$pb = New-Object System.Speech.Synthesis.PromptBuilder
$pb.StartVoice('Microsoft Irina Desktop')
$pb.AppendText('Привет! Сейчас будет фрагмент на английском языке.')
$pb.EndVoice()
$pb.AppendBreak([TimeSpan]::FromSeconds(1.5))
$pb.StartVoice('Microsoft David Desktop')
$pb.AppendText('Machine learning models can transcribe speech in many languages.')
$pb.EndVoice()
$pb.AppendBreak([TimeSpan]::FromSeconds(1.5))
$pb.StartVoice('Microsoft Irina Desktop')
$pb.AppendText('А теперь снова русский. Конец записи.')
$pb.EndVoice()
Save-Speech 'mixed_ru_en.wav' $pb

$s.Dispose()
Write-Host "Done → $dir"
