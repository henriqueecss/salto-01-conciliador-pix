Output demo.gif

Set Shell "powershell"
Set FontSize 14
Set Width 1000
Set Height 600
Set Theme "Dracula"
Set Padding 20

Sleep 500ms

Type "# Conciliador de Pix - Demo"
Enter
Sleep 1.5s

Type "python -m conciliador --pedidos data/pedidos.csv --extrato data/extrato.csv"
Enter
Sleep 5s

Type "# Saida em CSV:"
Enter
Sleep 500ms

Type "python -m conciliador --pedidos data/pedidos.csv --extrato data/extrato.csv --formato csv"
Enter
Sleep 5s

Type "# Testes: 111 passando, gabarito 31/31"
Enter
Sleep 500ms

Type "pytest tests/ -q"
Enter
Sleep 8s

Sleep 2s
