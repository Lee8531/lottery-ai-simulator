#!/usr/bin/env bash
set -euo pipefail

# ---- Parse arguments ----
DataDir="data/normalized"
ReportDir="reports/latest"
RecommendationDir="data/recommendations"
Game=""
DryRun=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        -DataDir)         DataDir="$2"; shift 2 ;;
        -ReportDir)       ReportDir="$2"; shift 2 ;;
        -RecommendationDir) RecommendationDir="$2"; shift 2 ;;
        -Game)            Game="$2"; shift 2 ;;
        -DryRun)          DryRun=true; shift ;;
        *)                echo "Unknown argument: $1"; exit 1 ;;
    esac
done

if [[ -z "$Game" ]]; then
    echo "Please specify -Game <code>." >&2; exit 1
fi

ALLOWED_GAMES="3d pl3 pl5 qxc qlc kl8 ssq dlt"
if ! echo "$ALLOWED_GAMES" | grep -qw "$Game"; then
    echo "Unsupported -Game '$Game'. Allowed: $ALLOWED_GAMES" >&2; exit 1
fi

# ---- Map game code to update/verify commands ----
case "$Game" in
    3d)  UpdateCmd="update-3d";  VerifyCmd="verify-recommend-3d";  Csv="$DataDir/fucai3d.csv"; ExtraArgs="" ;;
    pl3) UpdateCmd="update-pl3"; VerifyCmd="verify-recommend-pl3"; Csv="$DataDir/pl3.csv";      ExtraArgs="" ;;
    pl5) UpdateCmd="update-pl5"; VerifyCmd="verify-recommend-pl5"; Csv="$DataDir/pl5.csv";      ExtraArgs="" ;;
    qxc) UpdateCmd="update-qxc"; VerifyCmd="verify-recommend-qxc"; Csv="$DataDir/qxc.csv";      ExtraArgs="" ;;
    qlc) UpdateCmd="update-qlc"; VerifyCmd="verify-recommend-qlc"; Csv="$DataDir/qlc.csv";      ExtraArgs="" ;;
    kl8) UpdateCmd="update-kl8"; VerifyCmd="verify-recommend-kl8"; Csv="$DataDir/kl8.csv";      ExtraArgs="--pick-size 10" ;;
    ssq) UpdateCmd="update-ssq"; VerifyCmd="verify-recommend-ssq"; Csv="$DataDir/ssq.csv";      ExtraArgs="" ;;
    dlt) UpdateCmd="update-dlt"; VerifyCmd="verify-recommend-dlt"; Csv="$DataDir/dlt.csv";      ExtraArgs="" ;;
esac

# ---- Resolve Python executable ----
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"
export PYTHONPATH="src"
export PYTHONIOENCODING="utf-8"

# Prefer LOTTERY_CLI_EXE, then venv python, then system python
CLI_CMD="${LOTTERY_CLI_EXE:-}"
if [[ -z "$CLI_CMD" ]]; then
    VENV_PY="$REPO_ROOT/.venv/bin/python"
    if [[ -x "$VENV_PY" ]]; then
        CLI_CMD="$VENV_PY"
    else
        CLI_CMD="python"
    fi
fi
RUN_CMD=("$CLI_CMD" -m lottery_sim.cli)

invoke_lottery() {
    local name="$1"
    shift
    echo "[$name] ${RUN_CMD[*]} $*"
    if $DryRun; then return 0; fi
    "${RUN_CMD[@]}" "$@"
    local rc=$?
    if [[ $rc -ne 0 ]]; then
        echo "Command failed with exit code $rc: $name" >&2
        exit $rc
    fi
}

mkdir -p "$DataDir" "$ReportDir" "$RecommendationDir"

# ---- Step 1: Update data ----
invoke_lottery "update-$Game" "$UpdateCmd" --csv "$Csv"

# ---- Step 2: Verify recommendation records ----
gameDir="$RecommendationDir/$Game"
if [[ -d "$gameDir" ]]; then
    for recordFile in "$gameDir"/*.csv; do
        if [[ -f "$recordFile" ]]; then
            invoke_lottery "verify-$Game-$(basename "$recordFile" .csv)" \
                "$VerifyCmd" --csv "$Csv" --records "$recordFile" --output "$recordFile" $ExtraArgs
        fi
    done
fi

# ---- Step 3: Summarize recommendations ----
summaryPath="$ReportDir/recommendation-summary.txt"
recordPaths=()
if [[ -d "$RecommendationDir" ]]; then
    while IFS= read -r -d '' f; do
        recordPaths+=("$f")
    done < <(find "$RecommendationDir" -name "*.csv" -type f -print0 | sort -z)
fi

if [[ ${#recordPaths[@]} -gt 0 ]]; then
    summaryArgs=("summarize-recommendations" "--records")
    for p in "${recordPaths[@]}"; do
        summaryArgs+=("$p")
    done
    summaryArgs+=("--output" "$summaryPath")
    invoke_lottery "summarize-recommendations" "${summaryArgs[@]}"
else
    echo "[summarize-recommendations] no recommendation records found"
fi

echo "Update workflow finished for: $Game"
