# Process Nifty 50
Write-Host "Processing Nifty 50..." -ForegroundColor Cyan
python start.py --input nifty50_host --output processed_indicators
python generate_summary.py --input processed_indicators --output dashboard/public/summary.json

# Process Nifty 500
Write-Host "Processing Nifty 500..." -ForegroundColor Cyan
python start.py --input nifty500_host --output processed_indicators_500
python generate_summary.py --input processed_indicators_500 --output dashboard/public/summary_500.json

Write-Host "All processing complete!" -ForegroundColor Green
