import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from thefuzz import fuzz

# Imports locais dos módulos criados
import database
import cliente_api as api
import matcher

console = Console()

def show_menu():
    console.print("\n")
    menu_text = (
        "[bold cyan]1.[/bold cyan] Sincronizar bancos (API -> SQLite)\n"
        "[bold cyan]2.[/bold cyan] Busca por aproximação (Nome)\n"
        "[bold cyan]3.[/bold cyan] Busca por código com tolerância\n"
        "[bold cyan]4.[/bold cyan] Agrupar por similaridade de nomenclatura\n"
        "[bold cyan]5.[/bold cyan] Corrigir nome digitado\n"
        "[bold magenta]6. \\[BÔNUS][/bold magenta] Autocorreção simulada (Lote)\n"
        "[bold magenta]7. \\[BÔNUS][/bold magenta] Quiz de reconhecimento de distorção\n"
        "[bold magenta]8. \\[BÔNUS][/bold magenta] Exportar dicionário de sinônimos\n"
        "[bold red]0.[/bold red] Encerrar aplicação"
    )
    console.print(Panel(menu_text, title="[bold green]SISTEMA DE BUSCA APROXIMADA - BANCOS BRASIL[/bold green]", expand=False))

def menu_sync():
    console.print("[yellow]Buscando dados atualizados da API...[/yellow]")
    bancos_api = api.fetch_banks()
    if not bancos_api:
        console.print("[bold red]Falha na requisição. Verifique a conexão.[/bold red]")
        return
        
    database.save_banks(bancos_api)
    console.print(Panel(f"[bold green]Sucesso![/bold green] Foram processados e salvos [bold white]{len(bancos_api)}[/bold white] bancos no SQLite.", border_style="green"))

def menu_search_name():
    query = Prompt.ask("[cyan]Informe o nome ou termo para busca[/cyan]")
    results = matcher.find_similar_by_name(query)
    
    if not results:
        console.print("[red]Nenhum registro encontrado. Certifique-se de sincronizar a base.[/red]")
        return

    table = Table(title=f"Resultados de aproximação para: '{query}'", show_header=True, header_style="bold magenta")
    table.add_column("Código", style="dim")
    table.add_column("Nome Oficial do Banco")
    table.add_column("Score (0-100)", justify="right")
    table.add_column("Classificação")

    for item in results:
        b = item["bank"]
        score = item["score"]
        status = "[bold green]Correspondência exata[/bold green]" if score == 100 else "[yellow]Aproximado[/yellow]"
        table.add_row(str(b['code'] or 'N/A'), b['fullName'] or b['name'], f"{score}", status)
    
    console.print(table)

def menu_search_code():
    query = Prompt.ask("[cyan]Digite o código numérico procurado[/cyan]")
    exact, similar = matcher.find_similar_by_code(query)

    if exact:
        console.print(Panel(f"[bold green]Registro Exato Encontrado![/bold green]\n\n[bold]Banco:[/bold] {exact['fullName']}\n[bold]Código:[/bold] {exact['code']}", border_style="green"))
    elif similar:
        console.print("[yellow]Código exato indisponível. Sugestões por similaridade de digitação:[/yellow]")
        table = Table(show_header=True, header_style="bold yellow")
        table.add_column("Código Próximo")
        table.add_column("Nome Institucional")
        table.add_column("Score de Similaridade")
        
        for item in similar:
            b = item["bank"]
            table.add_row(str(b['code']), b['fullName'] or b['name'], f"{item['score']}")
        console.print(table)
    else:
        console.print("[red]Base de dados vazia.[/red]")

def menu_group_similarity():
    console.print("[yellow]Processando matriz de similaridade...[/yellow]")
    groups = matcher.group_by_similarity()
    
    if not groups:
        console.print("[yellow]Nenhuma similaridade redundante detectada.[/yellow]")
        return

    table = Table(title="Agrupamentos Sugeridos (Nomes Equivalentes)", show_header=True, header_style="bold green")
    table.add_column("Termo Representativo de Referência", style="bold cyan")
    table.add_column("Variações e Ramificações no Banco")

    for base_name, items in groups.items():
        var_string = " | ".join([b['name'] for b in items if b['name']])
        table.add_row(base_name, var_string)
        
    console.print(table)

def menu_correct_name():
    typed = Prompt.ask("[cyan]Digite o nome do banco com possíveis erros/omissões[/cyan]")
    bank, score = matcher.correct_name(typed)
    
    if bank:
        table = Table(title="Autocorreção Inteligente")
        table.add_column("Entrada do Usuário", style="red")
        table.add_column("Sugestão Sugerida", style="green")
        table.add_column("Confiança", justify="center")
        table.add_row(typed, bank['fullName'] or bank['name'], f"{score}%")
        console.print(table)
    else:
        console.print("[red]Não foi possível formular uma sugestão.[/red]")

def menu_bonus_batch():
    console.print("[magenta]Digite múltiplos nomes fictícios ou errados separados por vírgula:[/magenta]")
    entrada = Prompt.ask("Nomes em lote")
    lista = [n.strip() for n in entrada.split(",") if n.strip()]
    
    if not lista:
        return
        
    relatorio = matcher.process_batch_correction(lista)
    table = Table(title="Relatório de Processamento em Lote")
    table.add_column("Original Digitado", style="yellow")
    table.add_column("Sugestão Corrigida", style="green")
    table.add_column("Nível", justify="right")
    
    for r in relatorio:
        table.add_row(r["original"], r["suggested"], f"{r['confidence']}%")
    console.print(table)

def menu_bonus_quiz():
    distorted, original = matcher.generate_quiz_question()
    if not distorted:
        console.print("[red]Banco de dados desatualizado/vazio.[/red]")
        return
        
    console.print(Panel(f"Qual banco gerou o seguinte ruído? [bold red]{distorted}[/bold red]", title="🎮 DESAFIO QUIZ"))
    palpite = Prompt.ask("[cyan]Seu palpite[/cyan]")
    
    score = fuzz.token_sort_ratio(palpite.lower(), original.lower())
    if score == 100:
        console.print("[bold green]Excelente! Você decifrou com precisão exata![/bold green]")
    elif score >= 75:
        console.print(f"[bold yellow]Muito próximo! Resposta considerada correta. O nome era '{original}'.[/bold yellow]")
    else:
        console.print(f"[bold red]Incorreto! O nome correto do banco era '{original}'. Similaridade do palpite: {score}%[/bold red]")

def menu_bonus_export():
    total = matcher.export_synonyms_dictionary()
    console.print(f"[bold green]Arquivo 'sinonimos_bancos.txt' gerado com sucesso! {total} relacionamentos salvos.[/bold green]")

def main():
    database.init_db()
    
    while True:
        show_menu()
        opcao = Prompt.ask("Selecione uma operação", choices=["0", "1", "2", "3", "4", "5", "6", "7", "8"])
        
        if opcao == "0":
            console.print("[bold blue]Finalizando sistema operacional.[/bold blue]")
            sys.exit(0)
        elif opcao == "1":
            menu_sync()
        elif opcao == "2":
            menu_search_name()
        elif opcao == "3":
            menu_search_code()
        elif opcao == "4":
            menu_group_similarity()
        elif opcao == "5":
            menu_correct_name()
        elif opcao == "6":
            menu_bonus_batch()
        elif opcao == "7":
            menu_bonus_quiz()
        elif opcao == "8":
            menu_bonus_export()

if __name__ == "__main__":
    main()