#!/usr/bin/env bash
set -euo pipefail

# ---- Parse arguments ----
DataDir="data/normalized"
ReportDir="reports/latest"
RecommendationDir="data/recommendations"
ModelDir="data/models"
Game=""
All=false
Seed=20260505
Seeds="1,2,3,4,5"
Window=30
Count=10
MlMinHistory=30
MlMinTrain=200
MlTrainEpochs=8
MlBacktestEpochs=3
MlBacktestLimit=30
MlRetrainEvery=10
SkipNormalize=false
DryRun=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        -DataDir)            DataDir="$2"; shift 2 ;;
        -ReportDir)          ReportDir="$2"; shift 2 ;;
        -RecommendationDir)  RecommendationDir="$2"; shift 2 ;;
        -ModelDir)           ModelDir="$2"; shift 2 ;;
        -Game)               Game="$2"; shift 2 ;;
        -All)                All=true; shift ;;
        -Seed)               Seed="$2"; shift 2 ;;
        -Seeds)              Seeds="$2"; shift 2 ;;
        -Window)             Window="$2"; shift 2 ;;
        -Count)              Count="$2"; shift 2 ;;
        -MlMinHistory)       MlMinHistory="$2"; shift 2 ;;
        -MlMinTrain)         MlMinTrain="$2"; shift 2 ;;
        -MlTrainEpochs)      MlTrainEpochs="$2"; shift 2 ;;
        -MlBacktestEpochs)   MlBacktestEpochs="$2"; shift 2 ;;
        -MlBacktestLimit)    MlBacktestLimit="$2"; shift 2 ;;
        -MlRetrainEvery)     MlRetrainEvery="$2"; shift 2 ;;
        -SkipNormalize)      SkipNormalize=true; shift ;;
        -DryRun)             DryRun=true; shift ;;
        *)                   echo "Unknown argument: $1"; exit 1 ;;
    esac
done

if $All && [[ -n "$Game" ]]; then
    echo "Use either -Game <code> or -All, not both." >&2; exit 1
fi
if ! $All && [[ -z "$Game" ]]; then
    echo "Please specify -Game <code> or use -All explicitly." >&2; exit 1
fi

ALLOWED_GAMES="3d pl3 pl5 qxc qlc kl8 ssq dlt"
if [[ -n "$Game" ]] && ! echo "$ALLOWED_GAMES" | grep -qw "$Game"; then
    echo "Unsupported -Game '$Game'. Allowed: $ALLOWED_GAMES" >&2; exit 1
fi

# ---- Select games ----
if $All; then
    SELECTED_GAMES="3d pl3 pl5 qxc qlc kl8 ssq dlt"
else
    SELECTED_GAMES="$Game"
fi

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
    local outputFile="$2"
    shift 2
    echo "[$name] ${RUN_CMD[*]} $*"
    if $DryRun; then return 0; fi

    if [[ -n "$outputFile" ]]; then
        "${RUN_CMD[@]}" "$@" > "$outputFile"
        local rc=$?
        echo "  -> $outputFile"
    else
        "${RUN_CMD[@]}" "$@"
        local rc=$?
    fi

    if [[ $rc -ne 0 ]]; then
        echo "Command failed with exit code $rc: $name" >&2
        exit $rc
    fi
}

mkdir -p "$DataDir" "$ReportDir" "$RecommendationDir" "$ModelDir"

# ---- Process each game ----
for g in $SELECTED_GAMES; do
    case "$g" in
        3d)  Csv="$DataDir/fucai3d.csv"; ExtraArgs="" ;;
        pl3) Csv="$DataDir/pl3.csv";      ExtraArgs="" ;;
        pl5) Csv="$DataDir/pl5.csv";      ExtraArgs="" ;;
        qxc) Csv="$DataDir/qxc.csv";      ExtraArgs="" ;;
        qlc) Csv="$DataDir/qlc.csv";      ExtraArgs="" ;;
        kl8) Csv="$DataDir/kl8.csv";      ExtraArgs="--pick-size 10" ;;
        ssq) Csv="$DataDir/ssq.csv";      ExtraArgs="" ;;
        dlt) Csv="$DataDir/dlt.csv";      ExtraArgs="" ;;
    esac

    # Step 1: Update data (or assert file exists if SkipNormalize)
    if ! $SkipNormalize; then
        invoke_lottery "update-$g" "" "update-$g" --csv "$Csv"
    else
        if ! $DryRun && [[ ! -f "$Csv" ]]; then
            echo "Data file not found: $Csv. Run without -SkipNormalize first." >&2; exit 1
        fi
    fi

    # Step 2: Backtest
    invoke_lottery "backtest-$g" "$ReportDir/backtest-$g.txt" \
        "backtest-$g" --csv "$Csv" $ExtraArgs --seed "$Seed"

    # Step 3: Compare
    invoke_lottery "compare-$g" "$ReportDir/compare-$g.txt" \
        "compare-$g" --csv "$Csv" $ExtraArgs --seed "$Seed" --window "$Window"

    # Step 4: Stability
    invoke_lottery "stability-$g" "$ReportDir/stability-$g.txt" \
        "stability-$g" --csv "$Csv" $ExtraArgs --seeds "$Seeds" --window "$Window"

    # Step 5: Recommend
    invoke_lottery "recommend-$g" "$ReportDir/recommend-$g.txt" \
        "recommend-$g" --csv "$Csv" $ExtraArgs --seed "$Seed" --window "$Window" --count "$Count"

    # Step 6: Train ML
    mlModel="$ModelDir/$g-ml.json"
    invoke_lottery "train-ml-$g" "" \
        "train-ml-$g" --csv "$Csv" --model "$mlModel" --min-history "$MlMinHistory" --epochs "$MlTrainEpochs" $ExtraArgs

    # Step 7: Backtest ML
    invoke_lottery "backtest-ml-$g" "$ReportDir/backtest-ml-$g.txt" \
        "backtest-ml-$g" --csv "$Csv" --min-train "$MlMinTrain" --min-history "$MlMinHistory" \
        --limit "$MlBacktestLimit" --retrain-every "$MlRetrainEvery" --epochs "$MlBacktestEpochs" $ExtraArgs

    # Step 8: Recommend ML
    invoke_lottery "recommend-ml-$g" "$ReportDir/recommend-ml-$g.txt" \
        "recommend-ml-$g" --csv "$Csv" --model "$mlModel" --count "$Count" \
        --min-history "$MlMinHistory" --epochs "$MlTrainEpochs" $ExtraArgs

    # Step 9: Record ML recommendation
    invoke_lottery "record-ml-$g" "" \
        "record-recommend-ml-$g" --csv "$Csv" --model "$mlModel" --store "$RecommendationDir" \
        --count "$Count" --min-history "$MlMinHistory" --epochs "$MlTrainEpochs" $ExtraArgs

    # Step 10: Verify recommendation records
    gameDir="$RecommendationDir/$g"
    if [[ -d "$gameDir" ]]; then
        for recordFile in "$gameDir"/*.csv; do
            if [[ -f "$recordFile" ]]; then
                invoke_lottery "verify-$g-$(basename "$recordFile" .csv)" "" \
                    "verify-recommend-$g" --csv "$Csv" --records "$recordFile" --output "$recordFile" $ExtraArgs
            fi
        done
    fi

    # Step 11: Record recommendation
    invoke_lottery "record-$g" "" \
        "record-recommend-$g" --csv "$Csv" --store "$RecommendationDir" \
        --seed "$Seed" --window "$Window" --count "$Count" $ExtraArgs
done

# ---- Step 12: Summarize recommendations ----
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
    invoke_lottery "summarize-recommendations" "" "${summaryArgs[@]}"
else
    echo "[summarize-recommendations] no recommendation records found"
fi

echo "Daily workflow finished for: $SELECTED_GAMES"
