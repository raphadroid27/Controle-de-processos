"""
Script para análise completa de qualidade de código.

Executa múltiplas ferramentas de análise estática e formatação,
gerando um relatório detalhado em arquivo de texto.
"""

import argparse
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def parse_arguments():
    """
    Analisa e processa os argumentos fornecidos via linha de comando.
    """
    parser = argparse.ArgumentParser(
        description="Análise completa de qualidade de código com formatação automática."
    )
    parser.add_argument(
        "--src",
        default="src",
        help="Diretório do código fonte a ser analisado (padrão: src).",
    )
    parser.add_argument(
        "--no-format",
        action="store_true",
        help="Desativa a aplicação de formatações automáticas (black, isort, etc.).",
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Não gera o arquivo de relatório em TXT.",
    )
    parser.add_argument(
        "--format-only",
        action="store_true",
        help="Apenas aplica as formatações, sem executar as análises.",
    )
    parser.add_argument(
        "--tools",
        nargs="+",
        help="Executa apenas as ferramentas especificadas (ex: --tools pylint flake8).",
    )
    return parser.parse_args()


def check_tool_installed(tool_name):
    """
    Verifica se uma ferramenta está instalada e acessível no ambiente.
    Tenta verificar tanto como executável direto quanto como módulo Python.
    """
    # Prioriza a verificação de executáveis no PATH do sistema
    if shutil.which(tool_name):
        return True

    # Se não encontrado, tenta verificar como um módulo Python
    try:
        # A maioria das ferramentas suporta --version
        subprocess.run(
            [sys.executable, "-m", tool_name, "--version"],
            capture_output=True,
            check=True,
            text=True,
            timeout=10,
        )
        return True
    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        FileNotFoundError,
    ):
        # Fallback para ferramentas que não têm --version, tentando importá-las
        try:
            subprocess.run(
                [sys.executable, "-c", f"import {tool_name}"],
                capture_output=True,
                check=True,
                text=True,
                timeout=10,
            )
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False


def run_command(cmd, description, timeout=120, save_to_report=True, report_file=None):
    """
    Executa um comando no shell, captura a saída e gerencia os resultados.
    """
    print(f"\n{'='*60}")
    print(f"🔍 {description}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )

        output = ""
        if result.stdout:
            output += result.stdout
            print(result.stdout)
        # Algumas ferramentas (ex: copydetect) usam stderr para a saída padrão
        if result.stderr:
            output += result.stderr
            print(result.stderr)

        is_success = result.returncode == 0

        if save_to_report and report_file:
            with open(report_file, "a", encoding="utf-8") as f:
                f.write(f"\n{'='*60}\n")
                f.write(f"🔍 {description}\n")
                f.write(f"{'='*60}\n")
                f.write(f"Comando: {cmd}\n")
                f.write(f"Status: {'✅ Sucesso' if is_success else '❌ Erro/Aviso'}\n")
                f.write(f"Código de retorno: {result.returncode}\n")
                if output:
                    f.write(f"\nSaída:\n{output}\n")
                f.write("\n")

        return is_success
    except subprocess.TimeoutExpired:
        error_msg = f"⏰ Comando excedeu o tempo limite de {timeout}s"
        print(error_msg)
        if save_to_report and report_file:
            with open(report_file, "a", encoding="utf-8") as f:
                f.write(f"\n{description}: {error_msg}\n")
        return False
    except (subprocess.SubprocessError, OSError) as e:
        error_msg = f"❌ Erro ao executar: {e}"
        print(error_msg)
        if save_to_report and report_file:
            with open(report_file, "a", encoding="utf-8") as f:
                f.write(f"\n{description}: {error_msg}\n")
        return False
    except KeyboardInterrupt:
        print("\n🛑 Comando interrompido pelo usuário.")
        # Propaga a interrupção para que o script principal possa parar
        raise


def apply_auto_formatting(tools, src_path, report_file):
    """
    Aplica formatações automáticas no código usando autoflake, isort e black.
    """
    print("\n🎨 APLICANDO FORMATAÇÕES AUTOMÁTICAS")
    formatting_results = []

    if tools.get("autoflake"):
        success = run_command(
            f"python -m autoflake --remove-all-unused-imports "
            f"--remove-unused-variables --in-place --recursive {src_path}/",
            "Removendo imports e variáveis não utilizados (autoflake)",
            60,
            True,
            report_file,
        )
        formatting_results.append(("Autoflake", success))

    if tools.get("isort"):
        success = run_command(
            f"python -m isort {src_path}/ --profile black --skip-glob '**/*.pyc'",
            "Organizando imports (isort)",
            30,
            True,
            report_file,
        )
        formatting_results.append(("Isort", success))

    if tools.get("black"):
        success = run_command(
            f"python -m black {src_path}/ --line-length=88 --extend-exclude='\\.pyc$'",
            "Formatando código (Black)",
            60,
            True,
            report_file,
        )
        formatting_results.append(("Black", success))

    return formatting_results


def create_summary_report(report_file, tools, formatting_results, analysis_results):
    """
    Gera a seção de resumo no final do arquivo de relatório.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(report_file, "a", encoding="utf-8") as f:
        f.write(f"\n{'='*80}\n")
        f.write(f"RESUMO DA ANÁLISE DE CÓDIGO - {timestamp}\n")
        f.write(f"{'='*80}\n\n")

        f.write("📋 STATUS DAS FERRAMENTAS:\n")
        f.write("-" * 40 + "\n")
        for tool, installed in tools.items():
            status = "✅ Instalada" if installed else "❌ Não instalada"
            f.write(f"{tool:<20}: {status}\n")

        if formatting_results:
            f.write("\n🎨 RESULTADOS DA FORMATAÇÃO:\n")
            f.write("-" * 40 + "\n")
            for tool, success in formatting_results:
                status = "✅ Sucesso" if success else "❌ Falhou"
                f.write(f"{tool:<20}: {status}\n")

        if analysis_results:
            f.write("\n🔍 RESULTADOS DA ANÁLISE:\n")
            f.write("-" * 40 + "\n")
            for tool, success in analysis_results:
                status = "✅ Sucesso" if success else "❌ Falhou/Aviso"
                f.write(f"{tool:<20}: {status}\n")

        f.write(f"\n{'='*80}\n")
        f.write("📊 Análise completa finalizada!\n")
        f.write("Revise os resultados detalhados acima para identificar melhorias.\n")
        f.write(f"{'='*80}\n")


# pylint: disable=R0912,R0914,R0915,C0301
def main():
    """
    Função principal que orquestra a execução da análise.
    """
    args = parse_arguments()
    src_path = args.src

    if not Path(src_path).is_dir():
        print(f"❌ Erro: O diretório '{src_path}' não foi encontrado!")
        sys.exit(1)

    report_file = None
    if not args.no_report:
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = reports_dir / f"analise_codigo_{timestamp}.txt"

    print("🚀 Iniciando análise completa de qualidade de código...")
    if report_file:
        print(f"📄 Relatório será salvo em: {report_file}")

    all_tools = {
        "autoflake": check_tool_installed("autoflake"),
        "isort": check_tool_installed("isort"),
        "black": check_tool_installed("black"),
        "pylint": check_tool_installed("pylint"),
        "flake8": check_tool_installed("flake8"),
        "pydocstyle": check_tool_installed("pydocstyle"),
        "vulture": check_tool_installed("vulture"),
        "mypy": check_tool_installed("mypy"),
        "bandit": check_tool_installed("bandit"),
        "safety": check_tool_installed("safety"),
        "radon": check_tool_installed("radon"),
        "copydetect": check_tool_installed("copydetect"),
    }

    tools_to_run = all_tools
    if args.tools:
        invalid_tools = [tool for tool in args.tools if tool not in all_tools]
        if invalid_tools:
            print(f"❌ Ferramentas inválidas: {', '.join(invalid_tools)}")
            print(f"🔧 Ferramentas disponíveis: {', '.join(all_tools.keys())}")
            sys.exit(1)
        tools_to_run = {tool: all_tools.get(tool, False) for tool in args.tools}

    if report_file:
        with open(report_file, "w", encoding="utf-8") as f:
            f.write("RELATÓRIO DE ANÁLISE DE QUALIDADE DE CÓDIGO\n")
            f.write(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Diretório analisado: {src_path}\n")
            f.write(f"Argumentos: {' '.join(sys.argv[1:])}\n")
            f.write("=" * 80 + "\n\n")

    missing_tools = [tool for tool, installed in tools_to_run.items() if not installed]
    if missing_tools:
        msg = f"\n⚠️  Ferramentas não instaladas e serão puladas: {', '.join(missing_tools)}"
        print(msg)
        print(
            "💡 Para instalar, adicione-as a um requirements-dev.txt e execute: "
            "pip install -r requirements-dev.txt"
        )
        if report_file:
            with open(report_file, "a", encoding="utf-8") as f:
                f.write(f"{msg}\n\n")

    formatting_results = []
    analysis_results = []

    if not args.no_format:
        formatting_results = apply_auto_formatting(tools_to_run, src_path, report_file)

    if not args.format_only:
        print("\n🔍 EXECUTANDO ANÁLISE DE QUALIDADE E ESTILO")

        if tools_to_run.get("pylint"):

            success = run_command(
                f"python -m pylint {src_path} --disable=C0114,C0115,C0116,R0903,R0913 "
                f"--output-format=text --reports=n --score=y --jobs=0 --ignore-patterns='.*\\.pyc$'",
                "Análise completa com Pylint",
                300,
                not args.no_report,
                report_file,
            )
            analysis_results.append(("Pylint", success))

        if tools_to_run.get("flake8"):
            success = run_command(
                f"python -m flake8 {src_path}/ --max-line-length=88 "
                f"--ignore=E203,W503 --exclude=__pycache__,*.pyc",
                "Análise de estilo com Flake8",
                60,
                not args.no_report,
                report_file,
            )
            analysis_results.append(("Flake8", success))

        if tools_to_run.get("pydocstyle"):
            # pydocstyle já ignora arquivos que não terminam com .py por padrão
            success = run_command(
                f"python -m pydocstyle {src_path}/",
                "Análise de estilo de docstrings (Pydocstyle)",
                60,
                not args.no_report,
                report_file,
            )
            analysis_results.append(("Pydocstyle", success))

        if tools_to_run.get("vulture"):
            success = run_command(
                f"python -m vulture {src_path}/ --min-confidence 80 --exclude=*.pyc",
                "Detecção de código morto (Vulture)",
                60,
                not args.no_report,
                report_file,
            )
            analysis_results.append(("Vulture", success))

        print("\n⚡ ANÁLISE AVANÇADA, SEGURANÇA E MÉTRICAS")
        if tools_to_run.get("mypy"):
            success = run_command(
                f"python -m mypy {src_path}/ --ignore-missing-imports "
                f"--no-strict-optional --exclude='.*\\.pyc$'",
                "Verificação de tipos (MyPy)",
                120,
                not args.no_report,
                report_file,
            )
            analysis_results.append(("MyPy", success))

        if tools_to_run.get("bandit"):
            success = run_command(
                f"python -m bandit -r {src_path}/ --format screen --skip B101 -x '**/__pycache__/*'",  # pylint: disable=C0301
                "Análise de segurança de código (Bandit)",
                90,
                not args.no_report,
                report_file,
            )
            analysis_results.append(("Bandit", success))

        if tools_to_run.get("safety"):
            success = run_command(
                "python -m safety check --full-report",
                "Análise de segurança de dependências (Safety)",
                90,
                not args.no_report,
                report_file,
            )
            analysis_results.append(("Safety", success))

        if tools_to_run.get("radon"):
            exclude_pattern = "**/__pycache__/*"
            success_cc = run_command(
                f"python -m radon cc {src_path}/ -a --min=B -e '{exclude_pattern}'",
                "Complexidade ciclomática (Radon CC)",
                60,
                not args.no_report,
                report_file,
            )
            analysis_results.append(("Radon (CC)", success_cc))

            success_mi = run_command(
                f"python -m radon mi {src_path}/ -s -n B -e '{exclude_pattern}'",
                "Índice de Manutenibilidade (Radon MI)",
                60,
                not args.no_report,
                report_file,
            )
            analysis_results.append(("Radon (MI)", success_mi))

        if tools_to_run.get("copydetect"):
            # -e py garante que apenas arquivos .py sejam verificados
            success = run_command(
                f"copydetect -t {src_path} -n 25 -g 25 -e py",
                "Detecção de código duplicado (copydetect)",
                120,
                not args.no_report,
                report_file,
            )
            analysis_results.append(("copydetect", success))

    if report_file:
        create_summary_report(
            report_file, tools_to_run, formatting_results, analysis_results
        )

    print(f"\n{'='*60}")
    print("✅ Análise completa finalizada!")
    if report_file:
        print(f"📄 Relatório salvo em: {report_file}")
    print("📊 Revise a saída e o relatório para identificar melhorias.")
    if missing_tools:
        print(
            f"💡 Para instalar as ferramentas faltantes: pip install {' '.join(missing_tools)}"
        )
    print(f"{'='*60}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Análise interrompida pelo usuário. Saindo.")
        sys.exit(1)
    except (OSError, subprocess.SubprocessError, ValueError) as e:
        print(f"\n❌ Um erro inesperado e fatal ocorreu: {e}")
        sys.exit(1)
