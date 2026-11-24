Add-Type -AssemblyName System.Runtime.WindowsRuntime
[Windows.Media.SpeechSynthesis.SpeechSynthesizer, Windows.Media, ContentType = WindowsRuntime] | Out-Null

$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
})[0]

function Await-WinRt($winRtOp, $resultType) {
    $asTask = $asTaskGeneric.MakeGenericMethod($resultType)
    $netTask = $asTask.Invoke($null, @($winRtOp))
    $netTask.Wait(-1) | Out-Null
    return $netTask.Result
}

$synth = New-Object Windows.Media.SpeechSynthesis.SpeechSynthesizer
$voiceHeera = [Windows.Media.SpeechSynthesis.SpeechSynthesizer]::AllVoices | Where-Object { $_.DisplayName -match "Heera" } | Select-Object -First 1
$voiceDavid = [Windows.Media.SpeechSynthesis.SpeechSynthesizer]::AllVoices | Where-Object { $_.DisplayName -match "David" } | Select-Object -First 1

$alertsDir = "c:\project\hackasol\frontend\assets\alerts"
if (-not (Test-Path $alertsDir)) {
    New-Item -ItemType Directory -Path $alertsDir -Force | Out-Null
}

$speechPrompts = @(
    # Listening
    @{ File = "voice_listening_en.wav"; Voice = "David"; Text = "Listening. Please speak now." },
    @{ File = "voice_listening_hi.wav"; Voice = "Heera"; Text = "Sun rahe hain. Kripya boliye." },
    @{ File = "voice_listening_chg.wav"; Voice = "Heera"; Text = "Sunat hanw. Boliye." },

    # Paste WhatsApp
    @{ File = "voice_paste_whatsapp_en.wav"; Voice = "David"; Text = "Please paste the WhatsApp message here." },
    @{ File = "voice_paste_whatsapp_hi.wav"; Voice = "Heera"; Text = "Kripya WhatsApp message yahan paste karein." },
    @{ File = "voice_paste_whatsapp_chg.wav"; Voice = "Heera"; Text = "WhatsApp sandesh la yahan paste karav." },

    # Paste SMS
    @{ File = "voice_paste_sms_en.wav"; Voice = "David"; Text = "Please paste the SMS here." },
    @{ File = "voice_paste_sms_hi.wav"; Voice = "Heera"; Text = "Kripya SMS sandesh yahan paste karein." },
    @{ File = "voice_paste_sms_chg.wav"; Voice = "Heera"; Text = "SMS sandesh la yahan paste karav." },

    # Fallback options
    @{ File = "voice_fallback_en.wav"; Voice = "David"; Text = "Sorry, please tap one of these options." },
    @{ File = "voice_fallback_hi.wav"; Voice = "Heera"; Text = "Maaf kijiye, kripya inme se ek vikalp chunein." },
    @{ File = "voice_fallback_chg.wav"; Voice = "Heera"; Text = "Maaf karav, ema le ek thho chunav." }
)

foreach ($item in $speechPrompts) {
    if ($item.Voice -eq "David" -and $voiceDavid) {
        $synth.Voice = $voiceDavid
    } elseif ($voiceHeera) {
        $synth.Voice = $voiceHeera
    }

    $outPath = Join-Path $alertsDir $item.File
    $streamOp = $synth.SynthesizeTextToStreamAsync($item.Text)
    $stream = Await-WinRt $streamOp ([Windows.Media.SpeechSynthesis.SpeechSynthesisStream])

    $fs = [System.IO.File]::Create($outPath)
    $netStream = [System.IO.WindowsRuntimeStreamExtensions]::AsStreamForRead($stream)
    $netStream.CopyTo($fs)
    $fs.Close()
    $netStream.Close()

    $fi = Get-Item $outPath
    Write-Host "Generated prompt: $($item.File) ($($fi.Length) bytes)"
}
