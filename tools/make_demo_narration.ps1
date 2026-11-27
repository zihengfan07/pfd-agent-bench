param([Parameter(Mandatory=$true)][string]$WorkDir)
$ErrorActionPreference = 'Stop'
$narrationPath = Join-Path $WorkDir 'narration.json'
$segments = Get-Content -LiteralPath $narrationPath -Raw -Encoding UTF8 | ConvertFrom-Json
$voice = New-Object -ComObject SAPI.SpVoice
$voices = @{en='Microsoft Zira Desktop'; zh='Microsoft Huihui Desktop'}
foreach ($lang in @('en','zh')) {
    $selected = @($voice.GetVoices() | Where-Object { $_.GetDescription().StartsWith($voices[$lang]) })
    if ($selected.Count -ne 1) { throw "Missing voice: $($voices[$lang])" }
    $voice.Voice = $selected[0]
    $voice.Rate = 0
    for ($i = 0; $i -lt $segments.Count; $i++) {
        $stream = New-Object -ComObject SAPI.SpFileStream
        $format = New-Object -ComObject SAPI.SpAudioFormat
        $format.Type = 22
        $stream.Format = $format
        $target = [IO.Path]::GetFullPath((Join-Path $WorkDir "$lang-$i.wav"))
        $stream.Open($target, 3, $false)
        try {
            $voice.AudioOutputStream = $stream
            [void]$voice.Speak($segments[$i].$lang)
        } finally { $stream.Close() }
    }
}
Write-Output 'Bilingual voice tracks generated.'
