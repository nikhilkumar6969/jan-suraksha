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

$lessonsDir = "c:\project\hackasol\frontend\assets\lessons"
if (-not (Test-Path $lessonsDir)) {
    New-Item -ItemType Directory -Path $lessonsDir -Force | Out-Null
}

$lessonAudios = @(
    # 1. OTP
    @{ File = "lesson_otp_hi.wav"; Voice = "Heera"; Text = "OTP kya hai? OTP yaani One Time Password bank dwara bheja gaya 6 anko ka suraksha code hai. Yeh aapke bank khate ki chaabi hai. Asli bank ya police kabhi bhi OTP nahi maangte. Koi bhi phone par OTP maange to turant call kaatein aur kisi ko na batayein." },
    @{ File = "lesson_otp_chg.wav"; Voice = "Heera"; Text = "OTP ka hothe? OTP apan bank khata ke gupt chaabi aay. Bank wale ya police kabhu phone ma OTP nai maangay. Kono phone ma OTP maange ta turte call kaatav. OTP batabe ta khata pura khaali ho jaahi." },
    @{ File = "lesson_otp_en.wav"; Voice = "David"; Text = "What is OTP? OTP is a 6 digit confidential verification code sent by your bank. It acts as the digital key to your money. Banks or police will never ask for your OTP. If anyone asks for OTP over a call, hang up immediately." },

    # 2. ATM PIN
    @{ File = "lesson_atm_pin_hi.wav"; Voice = "Heera"; Text = "ATM PIN kaise surakshit rakhein? ATM PIN aapka 4 anko ka gupt number hai. Ise kabhi card ke peeche na likhein. ATM machine par paise nikaalte samay keypad ko hamesha dusre haath se dhankein. Kisi bhi anjaan vyakti ko apna PIN na batayein." },
    @{ File = "lesson_atm_pin_chg.wav"; Voice = "Heera"; Text = "ATM PIN la kaise bacha ke rakhav? ATM PIN 4 ank ke gupt code hothe. Card ke paachhu PIN jhan likhav. ATM machine ma paisa nikaalat samay keypad la haath le dhank lev. Kono anjaan mankhe la apan PIN jhan batawav." },
    @{ File = "lesson_atm_pin_en.wav"; Voice = "David"; Text = "How to keep your ATM PIN safe? Your 4 digit ATM PIN is strictly confidential. Never write it on the card. Always cover the keypad with your hand while entering your PIN at the ATM, and never take help from strangers." },

    # 3. UPI PIN
    @{ File = "lesson_upi_pin_hi.wav"; Voice = "Heera"; Text = "UPI PIN kab daalna chahiye? Swarna niyam: PIN daala matlab paisa kata. UPI PIN sirf paise bhejne ke liye hota hai. Kisi se paise lene ya cashback paane ke liye PIN ki koi zaroorat nahi hoti. Agar koi paise paane ke liye PIN maange to saaf mana karein." },
    @{ File = "lesson_upi_pin_chg.wav"; Voice = "Heera"; Text = "UPI PIN kab daarna chaahi? Sona kas niyam: PIN daaris ta paisa ge! UPI PIN sirif paisa bheje bar lagthe. Paisa paaye bar kabhu PIN nai laage. Kono paisa aahi kahike PIN maange ta turte mana karav." },
    @{ File = "lesson_upi_pin_en.wav"; Voice = "David"; Text = "When should you enter your UPI PIN? Golden rule: Entering your PIN means money goes OUT. You only enter your PIN to send money, NEVER to receive money or cashbacks. Never enter your PIN on anyones instructions." },

    # 4. QR Code
    @{ File = "lesson_qr_code_hi.wav"; Voice = "Heera"; Text = "QR Code Fraud kya hai? Dhyan dein, QR code scan karne se kabhi paise nahi aate. Thag QR bhejkar kehte hain ise scan karo to paise milenge. QR scan karne ka matlab hamesha aapke khate se paisa katna hota hai. Kisi anjaan ka QR kabhi scan na karein." },
    @{ File = "lesson_qr_code_chg.wav"; Voice = "Heera"; Text = "QR code thagi ka hothe? Dhyan dev, QR code scan kare le paisa nai aaway, ulta cut jaathe. Thag man QR bhej ke lalach dethin. Anjaan mankhe ke bheje QR la paisa paaye bar kabhu scan jhan karav." },
    @{ File = "lesson_qr_code_en.wav"; Voice = "David"; Text = "What is QR Code Fraud? Scanning a QR code always deducts money from your account. Scammers send QR codes claiming you will receive prizes. Never scan an unknown QR code to receive funds." },

    # 5. Fake Bank Call
    @{ File = "lesson_fake_bank_call_hi.wav"; Voice = "Heera"; Text = "Fake Bank Call kaise pehchanein? Thag bank officer bankar phone karte hain ki aapka khata ya SIM do ghante me band ho jayega. Asli bank kabhi phone par aisi dhamki nahi deta aur na hi OTP ya AnyDesk app maangta hai. Aisi call turant kaatein." },
    @{ File = "lesson_fake_bank_call_chg.wav"; Voice = "Heera"; Text = "Farzi bank call la kaise pehchanav? Thag man bank ke babu ban ke kahithan ki tor khata do ghanta ma band ho jaahi. Asli bank kabhu aisan dhamki nai deway au na AnyDesk app download karwaay. Phone turte kaatav." },
    @{ File = "lesson_fake_bank_call_en.wav"; Voice = "David"; Text = "How to identify Fake Bank Calls? Fraudsters pretend to be bank managers threatening that your account or SIM will be blocked. Genuine banks never threaten you or demand OTPs and remote screen sharing apps. Disconnect immediately." }
)

foreach ($item in $lessonAudios) {
    if ($item.Voice -eq "David" -and $voiceDavid) {
        $synth.Voice = $voiceDavid
    } elseif ($voiceHeera) {
        $synth.Voice = $voiceHeera
    }

    $outPath = Join-Path $lessonsDir $item.File
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
