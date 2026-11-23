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
    # UPI PIN
    @{ File = "alert_upi_pin_hi.wav"; Voice = "Heera"; Text = "Savdhaan! Kisi ko bhi apna UPI PIN na batayein aur na hi darj karein. Paise paane ke liye PIN ki zaroorat nahi hoti." },
    @{ File = "alert_upi_pin_chg.wav"; Voice = "Heera"; Text = "Bhaari khatra! Caller tor se UPI PIN maange ke chaal chalat he. Kabhu apan PIN jhan daarav." },
    @{ File = "alert_upi_pin_en.wav"; Voice = "David"; Text = "Warning! Never enter or disclose your UPI PIN. UPI PIN is never needed to receive money." },

    # OTP
    @{ File = "alert_otp_hi.wav"; Voice = "Heera"; Text = "Savdhaan! Kisi ko bhi apna OTP ya bank verification code na batayein. Call turant kaatein." },
    @{ File = "alert_otp_chg.wav"; Voice = "Heera"; Text = "Savdhaan! Tor gupt OTP kakro le jhan batawav. Phone la turte kaatav." },
    @{ File = "alert_otp_en.wav"; Voice = "David"; Text = "Alert! Never share your OTP or bank codes. Hang up the call immediately." },

    # Police / Digital Arrest
    @{ File = "alert_police_hi.wav"; Voice = "Heera"; Text = "Chetavani! Farzi police ya digital arrest ki dhamki se na darein. Call turant kaatein." },
    @{ File = "alert_police_chg.wav"; Voice = "Heera"; Text = "Jhan darwav! Farzi police ya digital arrest ke dhamki ma jhan aavav. Call la turte kaatav." },
    @{ File = "alert_police_en.wav"; Voice = "David"; Text = "Alert! Do not fall for fake police or arrest threats. Hang up immediately." },

    # Remote Access
    @{ File = "alert_remote_access_hi.wav"; Voice = "Heera"; Text = "Satark rahein! Koi bhi agyaat app ya AnyDesk download na karein aur screen share na karein." },
    @{ File = "alert_remote_access_chg.wav"; Voice = "Heera"; Text = "Satark rahav! Kono anjaan app download jhan karav au screen share jhan karav." },
    @{ File = "alert_remote_access_en.wav"; Voice = "David"; Text = "Warning! Do not install any unknown apps or share your screen." },

    # Extortion / Money Demand
    @{ File = "alert_extortion_hi.wav"; Voice = "Heera"; Text = "Chetavani! Kisi anjaan ko paise ya online transfer na karein. Call turant kaatein." },
    @{ File = "alert_extortion_chg.wav"; Voice = "Heera"; Text = "Chetavani! Kakro bahkaave ma aake paisa transfer jhan karav. Call turte kaatav." },
    @{ File = "alert_extortion_en.wav"; Voice = "David"; Text = "Warning! Do not transfer money or pay any caller. Disconnect immediately." },

    # Bank KYC
    @{ File = "alert_bank_kyc_hi.wav"; Voice = "Heera"; Text = "Chetavani! Bank kabhi phone par account band karne ki dhamki nahi deta. Call kaatein." },
    @{ File = "alert_bank_kyc_chg.wav"; Voice = "Heera"; Text = "Chetavani! Bank kabhu phone ma khata band kare ke dhamki nai deway. Call kaatav." },
    @{ File = "alert_bank_kyc_en.wav"; Voice = "David"; Text = "Caution! Banks never threaten account suspension over the phone. Hang up." }
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
    Write-Host "Generated: $($item.File) ($($fi.Length) bytes)"
}
