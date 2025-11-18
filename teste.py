"""
Projeto: Python + MySQL — Script único completo
Conteúdo:
- Cria banco de dados e usuário (opcional, requer acesso root)
- Cria tabela 'estudante'
- Fornece um menu interativo para CRUD (usando usuário app/senai)
- Instruções de uso no topo

Requisitos:
- Python 3.8+
- mysql-connector-python

Instalação das dependências:
    pip install mysql-connector-python

Como usar:
1) Para apenas usar o app (assumindo que o BD e usuário já existem):
    python python_mysql_full_project.py --run --host localhost --user senai --password 1234 --database senai

2) Para executar o setup (criar BD, tabela e usuário) — você precisa das credenciais root do MySQL:
    python python_mysql_full_project.py --setup --root-user root --root-password <SUA_SENHA_ROOT> --host localhost --new-db senai --new-user senai --new-pass 1234

3) Você também pode executar o script sem argumentos e seguir as instruções interativas.

Observações de segurança:
- Usar senhas em linha de comando pode expor credenciais em histórico do shell. Prefira rodar sem argumentos e digitar senhas quando solicitado.
- Este script foi feito para ambientes de aprendizado. Em produção, não armazene senhas em texto puro e utilize conexões seguras.

"""

import argparse
import getpass
import sys
import mysql.connector
from mysql.connector import errorcode
from tabulate import tabulate

# ------------------------ Helpers ------------------------

def safe_input(prompt, hide=False):
    try:
        if hide:
            return getpass.getpass(prompt)
        return input(prompt)
    except KeyboardInterrupt:
        print("\nOperação cancelada pelo usuário.")
        sys.exit(0)


# ------------------------ Database operations ------------------------

def connect_db(host, user, password, database=None):
    """Retorna uma conexão mysql.connector.connect()."""
    cfg = {
        'host': host,
        'user': user,
        'password': password,
        'raise_on_warnings': True,
    }
    if database:
        cfg['database'] = database
    try:
        conn = mysql.connector.connect(**cfg)
        return conn
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Erro: acesso negado — verifique usuário/senha.")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Erro: banco de dados não existe.")
        else:
            print(f"Erro de conexão: {err}")
        return None


def create_database(conn, db_name):
    cursor = conn.cursor()
    try:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` DEFAULT CHARACTER SET 'utf8mb4'")
        print(f"Banco de dados '{db_name}' criado (ou já existia).")
    except mysql.connector.Error as err:
        print(f"Falha ao criar o banco de dados: {err}")
        raise
    finally:
        cursor.close()


def create_user_and_grant(conn, username, password, db_name, host='localhost'):
    cursor = conn.cursor()
    try:
        # Criar usuário
        cursor.execute("SELECT COUNT(*) FROM mysql.user WHERE user = %s AND host = %s", (username, host))
        exists = cursor.fetchone()[0]
        if not exists:
            cursor.execute(f"CREATE USER %s@%s IDENTIFIED BY %s", (username, host, password))
            print(f"Usuário '{username}'@'{host}' criado.")
        else:
            print(f"Usuário '{username}'@'{host}' já existe. Não será criado, apenas atualizaremos privilégios.")

        # Dar privilégios
        cursor.execute(f"GRANT ALL PRIVILEGES ON `{db_name}`.* TO %s@%s", (username, host))
        cursor.execute("FLUSH PRIVILEGES")
        conn.commit()
        print(f"Privilégios concedidos ao usuário '{username}' para o DB '{db_name}'.")
    except mysql.connector.Error as err:
        print(f"Erro ao criar usuário ou conceder privilégios: {err}")
        conn.rollback()
        raise
    finally:
        cursor.close()


def create_table_estudante(conn):
    cursor = conn.cursor()
    try:
        sql = (
            "CREATE TABLE IF NOT EXISTS estudante ("
            "  matricula VARCHAR(5) NOT NULL,
            "  nome VARCHAR(100) NOT NULL,
            "  PRIMARY KEY (matricula)"
            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"
        )
        # Note: concatenated as one string to avoid syntax issues
        sql = "CREATE TABLE IF NOT EXISTS estudante ( matricula VARCHAR(5) NOT NULL, nome VARCHAR(100) NOT NULL, PRIMARY KEY (matricula) ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"
        cursor.execute(sql)
        conn.commit()
        print("Tabela 'estudante' criada (ou já existia).")
    except mysql.connector.Error as err:
        print(f"Erro ao criar tabela: {err}")
        conn.rollback()
        raise
    finally:
        cursor.close()


# ------------------------ CRUD operations ------------------------

def insert_estudante(conn, matricula, nome):
    cursor = conn.cursor()
    try:
        sql = "INSERT INTO estudante (matricula, nome) VALUES (%s, %s)"
        cursor.execute(sql, (matricula, nome))
        conn.commit()
        print("Inserção realizada com sucesso.")
    except mysql.connector.Error as err:
        print(f"Erro ao inserir: {err}")
        conn.rollback()
    finally:
        cursor.close()


def select_all(conn):
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT matricula, nome FROM estudante ORDER BY matricula")
        rows = cursor.fetchall()
        if rows:
            print(tabulate(rows, headers=["Matricula", "Nome"], tablefmt="grid"))
        else:
            print("Nenhum registro encontrado.")
    except mysql.connector.Error as err:
        print(f"Erro ao selecionar: {err}")
    finally:
        cursor.close()


def select_one(conn, matricula):
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT matricula, nome FROM estudante WHERE matricula = %s", (matricula,))
        row = cursor.fetchone()
        if row:
            print(tabulate([row], headers=["Matricula", "Nome"], tablefmt="grid"))
        else:
            print("Registro não encontrado.")
    except mysql.connector.Error as err:
        print(f"Erro ao selecionar: {err}")
    finally:
        cursor.close()


def update_estudante(conn, matricula, novo_nome):
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE estudante SET nome = %s WHERE matricula = %s", (novo_nome, matricula))
        conn.commit()
        if cursor.rowcount:
            print("Atualização realizada com sucesso.")
        else:
            print("Nenhum registro atualizado (verifique a matrícula).")
    except mysql.connector.Error as err:
        print(f"Erro ao atualizar: {err}")
        conn.rollback()
    finally:
        cursor.close()


def delete_estudante(conn, matricula):
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM estudante WHERE matricula = %s", (matricula,))
        conn.commit()
        if cursor.rowcount:
            print("Registro deletado com sucesso.")
        else:
            print("Nenhum registro deletado (verifique a matrícula).")
    except mysql.connector.Error as err:
        print(f"Erro ao deletar: {err}")
        conn.rollback()
    finally:
        cursor.close()


# ------------------------ Interactive menu ------------------------

def app_menu(conn):
    while True:
        print("\n--- MENU: CRUD de estudante ---")
        print("1) Listar todos")
        print("2) Consultar por matrícula")
        print("3) Inserir estudante")
        print("4) Atualizar nome do estudante")
        print("5) Deletar estudante")
        print("6) Sair")
        escolha = safe_input("Escolha uma opção (1-6): ")
        if escolha == '1':
            select_all(conn)
        elif escolha == '2':
            m = safe_input("Matrícula: ")
            select_one(conn, m)
        elif escolha == '3':
            m = safe_input("Matrícula (até 5 chars): ")
            if len(m) > 5:
                print("Matrícula deve ter no máximo 5 caracteres.")
                continue
            n = safe_input("Nome: ")
            insert_estudante(conn, m, n)
        elif escolha == '4':
            m = safe_input("Matrícula: ")
            n = safe_input("Novo nome: ")
            update_estudante(conn, m, n)
        elif escolha == '5':
            m = safe_input("Matrícula: ")
            confirma = safe_input(f"Confirmar exclusão de '{m}'? (s/N): ")
            if confirma.lower() == 's':
                delete_estudante(conn, m)
            else:
                print("Exclusão cancelada.")
        elif escolha == '6':
            print("Saindo...")
            break
        else:
            print("Opção inválida. Tente novamente.")


# ------------------------ Main / CLI ------------------------

def run_setup(args):
    host = args.host
    root_user = args.root_user
    if args.root_password:
        root_password = args.root_password
    else:
        root_password = safe_input("Senha root do MySQL: ", hide=True)

    new_db = args.new_db or safe_input("Nome do novo banco de dados a criar: ")
    new_user = args.new_user or safe_input("Nome do novo usuário a criar: ")
    if args.new_pass:
        new_pass = args.new_pass
    else:
        new_pass = safe_input("Senha para o novo usuário: ", hide=True)

    print("Conectando como root...")
    conn_root = connect_db(host, root_user, root_password)
    if not conn_root:
        print("Não foi possível conectar com as credenciais root. Abortando setup.")
        return

    try:
        create_database(conn_root, new_db)
        create_user_and_grant(conn_root, new_user, new_pass, new_db)
    finally:
        conn_root.close()

    # Criar tabela usando o usuário criado (ou root)
    print("Conectando ao novo banco para criar tabelas...")
    conn_app = connect_db(host, new_user, new_pass, database=new_db)
    if not conn_app:
        print("Não foi possível conectar com o novo usuário para criar tabelas. Verifique privilégios.")
        return
    try:
        create_table_estudante(conn_app)
    finally:
        conn_app.close()

    print("Setup concluído com sucesso.")


def run_app(args):
    host = args.host
    user = args.user
    if args.password:
        password = args.password
    else:
        password = safe_input("Senha do usuário: ", hide=True)

    db = args.database
    if not db:
        db = safe_input("Banco de dados: ")

    conn = connect_db(host, user, password, database=db)
    if not conn:
        print("Falha ao conectar com as credenciais fornecidas.")
        return

    try:
        app_menu(conn)
    finally:
        conn.close()


def parse_args():
    p = argparse.ArgumentParser(description='Script completo Python <-> MySQL (CRUD + setup)')
    p.add_argument('--host', default='localhost', help='Host do MySQL (default: localhost)')

    sub = p.add_mutually_exclusive_group()
    sub.add_argument('--setup', action='store_true', help='Executar setup (criar DB e usuário). Requer root).')
    sub.add_argument('--run', action='store_true', help='Executar app (menu CRUD).')

    # Setup-specific
    p.add_argument('--root-user', default='root', help='Usuário root para o setup (default: root)')
    p.add_argument('--root-password', help='Senha root (evite usar em linha de comando)')
    p.add_argument('--new-db', help='Nome do banco a ser criado no setup')
    p.add_argument('--new-user', help='Nome do usuário a ser criado no setup')
    p.add_argument('--new-pass', help='Senha do usuário a ser criado no setup')

    # Run-specific (app)
    p.add_argument('--user', help='Usuário para conectar ao app (ex: senai)')
    p.add_argument('--password', help='Senha do usuário do app (evite usar em linha de comando)')
    p.add_argument('--database', help='Banco de dados a usar (ex: senai)')

    return p.parse_args()


def main():
    args = parse_args()
    # Se nenhum argumento --setup ou --run foi passado, mostra menu interativo de escolha
    if not args.setup and not args.run:
        print("Bem-vindo — escolha o que deseja fazer:")
        print("1) Executar setup (criar DB, usuário e tabela) — requer credenciais root.")
        print("2) Executar app (conectar e usar CRUD)")
        escolha = safe_input("Escolha (1/2): ")
        if escolha == '1':
            args.setup = True
            # pedir host/root info
            args.host = safe_input("Host (default: localhost): ") or 'localhost'
            args.root_user = safe_input("Usuário root (default: root): ") or 'root'
            args.root_password = safe_input("Senha root: ", hide=True)
            args.new_db = safe_input("Novo DB (ex: senai): ")
            args.new_user = safe_input("Novo usuário (ex: senai): ")
            args.new_pass = safe_input("Senha do novo usuário: ", hide=True)
            run_setup(args)
            return
        elif escolha == '2':
            args.run = True
            args.host = safe_input("Host (default: localhost): ") or 'localhost'
            args.user = safe_input("Usuário (ex: senai): ")
            args.password = safe_input("Senha: ", hide=True)
            args.database = safe_input("Banco (ex: senai): ")
            run_app(args)
            return
        else:
            print("Opção inválida. Saindo.")
            return

    if args.setup:
        run_setup(args)
    elif args.run:
        # garantir que user/database sejam preenchidos
        if not args.user or not args.database:
            # perguntar interativamente
            args.host = args.host or safe_input("Host (default: localhost): ") or 'localhost'
            args.user = args.user or safe_input("Usuário (ex: senai): ")
            args.password = args.password or safe_input("Senha: ", hide=True)
            args.database = args.database or safe_input("Banco (ex: senai): ")
        run_app(args)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nPrograma interrompido pelo usuário.')
