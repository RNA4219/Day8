param([string]$Root = $env:REPORT_ROOT,[string[]]$ReposFull=@(
  "RNA4219/portfolio","RNA4219/planting-planner","RNA4219/llm-generic-bot",
  "RNA4219/deterministic_32","RNA4219/llm_orch","RNA4219/workflow-cookbook",
  "RNA4219/Day8","RNA4219/imgponic","RNA4219/katamari","RNA4219/taskest"))
# 新規プロジェクトへ持ち込む際は Root/ReposFull を引数・環境変数で必ず上書きし、PAT 付トークンを GITHUB_TOKEN に設定すること。
if(-not $Root){$Root=Join-Path (Split-Path -Parent $PSScriptRoot) ".report-work"}
$tz=[System.TimeZoneInfo]::FindSystemTimeZoneById("Tokyo Standard Time")
$now=[System.TimeZoneInfo]::ConvertTime([datetime]::UtcNow,$tz)
$start=(Get-Date -Date $now.Date.AddDays(-1) -Format "yyyy-MM-ddT00:00:00zzz")
$end=(Get-Date -Date $now.Date.AddSeconds(-1) -Format "yyyy-MM-ddT23:59:59zzz")
$out=Join-Path $Root "logs/$($now.ToString('yyyyMMdd-HHmm'))"
$details=Join-Path $out "details"
New-Item -ItemType Directory -Force -Path $details | Out-Null
if($env:GITHUB_TOKEN){git config --global url."https://$($env:GITHUB_TOKEN)@github.com/".insteadOf "https://github.com/" | Out-Null}
$pathspec=@(".",":(exclude)node_modules/**",":(exclude)dist/**",":(exclude)build/**",":(exclude).next/**",":(exclude)coverage/**",":(exclude)**/*.min.*",":(exclude)**/*.map",":(exclude)**/*.lock",":(exclude)**/*.svg",":(exclude)**/__snapshots__/**")
$rows=$ReposFull | ForEach-Object -Parallel {
  param($full,$Root,$Start,$End,$Pathspec,$Details)
  function GetDefaultBranch($dir){$ref=(& git -C $dir symbolic-ref --quiet refs/remotes/origin/HEAD 2>$null);if($LASTEXITCODE -eq 0 -and $ref){return ($ref -replace 'refs/remotes/origin/','')}
    $heads=(& git -C $dir branch -r) -join "`n";if($heads -match 'origin/main'){return 'main'};if($heads -match 'origin/master'){return 'master'};'main'}
  $owner,$name=$full -split "/";$dir=Join-Path $Root $name
  if(Test-Path $dir){git -C $dir fetch --all --prune --quiet | Out-Null}else{git clone --filter=blob:none --quiet "https://github.com/$owner/$name.git" $dir | Out-Null}
  $branch=GetDefaultBranch $dir
  $commits=git -C $dir log --no-merges --since=$Start --until=$End --pretty=format:'%H,%ad,"%s",%an' --date=iso-strict "origin/$branch" -- $Pathspec
  $commitCount=if($commits){($commits -split "`n").Count}else{0}
  $files=git -C $dir log --no-merges --since=$Start --until=$End --pretty=tformat: --name-only "origin/$branch" -- $Pathspec | Where-Object {$_} | Sort-Object -Unique
  $adds=0;$dels=0
  git -C $dir log --no-merges --since=$Start --until=$End --format=tformat: --numstat "origin/$branch" -- $Pathspec | ForEach-Object {
    if($_ -match '^\s*(\d+|-)\s+(\d+|-)\s+(.+)$'){if($matches[1] -ne '-'){$adds+=[int]$matches[1]};if($matches[2] -ne '-'){$dels+=[int]$matches[2]}}
  }
  $commitFile=Join-Path $Details "$name-commits.csv";$fileList=Join-Path $Details "$name-files.csv"
  "hash,date,subject,author" | Set-Content $commitFile -Encoding UTF8
  if($commits){($commits -split "`n") | Add-Content $commitFile -Encoding UTF8}
  "file" | Set-Content $fileList -Encoding UTF8
  if($files){$files | Add-Content $fileList -Encoding UTF8}
  [pscustomobject]@{Repo=$name;Commits=$commitCount;Files=$files.Count;Additions=$adds;Deletions=$dels;Net=$adds-$dels}
} -ThrottleLimit 4 -ArgumentList $Root,$Start,$End,$pathspec,$details
$rows=$rows | Sort-Object Repo
$sumC=($rows|Measure-Object Commits -Sum).Sum;$sumF=($rows|Measure-Object Files -Sum).Sum;$sumA=($rows|Measure-Object Additions -Sum).Sum;$sumD=($rows|Measure-Object Deletions -Sum).Sum;$sumN=$sumA-$sumD
$rows | Export-Csv -NoTypeInformation -Encoding UTF8 (Join-Path $out "summary.csv")
$md=@("# 24時間アクティビティ ($start ～ $end)","","- **Commits:** $sumC","- **Files changed:** $sumF","- **Additions / Deletions / Net:** $sumA / $sumD / $sumN","","| Repo | Commits | Files | + | - | Net |","|---|---:|---:|---:|---:|---:|")
foreach($r in ($rows | Sort-Object Commits -Descending)){$md+="| $($r.Repo) | $($r.Commits) | $($r.Files) | $($r.Additions) | $($r.Deletions) | $($r.Net) |"}
$md+="";$md+="> 詳細は `details/` を参照。除外: node_modules/dist/build/lock/min/map/svg/snapshots"
$md -join "`n" | Set-Content (Join-Path $out "summary.md") -Encoding UTF8
Write-Host "Done: $out" -ForegroundColor Green
