from datetime import datetime
from flask import Flask,  request
from furl import furl
import mysql.connector
import os


app = Flask(__name__)


db_config = {
    "database": os.environ["DB_DATABASE"],
    "user": os.environ["DB_USER"],
    "host": os.environ["DB_HOST"],
    "passwd": os.environ["DB_PASSWORD"],
}
pool = mysql.connector.pooling.MySQLConnectionPool(pool_name="pool_mysql", pool_size=32, **db_config)


@app.route("/clientes/<id>/transacoes", methods=["POST"])
def transacoes(id):
    f = furl(request.url)
    if len(f.args) != 3:
        return "informacoes incorretas", 450
    try:
        valor = int(f.args["valor"])
    except:
        return "valor deve ser um número inteiro", 400   
    tipo = f.args["tipo"]
    if tipo not in ["c", "d"]:
        return "tipo deve ser c ou d", 401
    descricao = f.args["descricao"]
    if len(descricao) > 10:
        return "descrição deve ter no máximo 10 caracteres", 402
    
    conexao = pool.get_connection()
    cursor = conexao.cursor()
    try:
        cursor.execute(f"SELECT saldo, limite FROM clientes WHERE id = {id}")
    except:
        conexao.close()
        return "não foi possível acessar o banco de dados", 500
    dados = cursor.fetchall()
    if not dados:
        conexao.close()
        return "id não existente", 404
    
    saldo = dados[0][0]
    limite = dados[0][1]
    
    if tipo == "d":
        if saldo - valor < (-limite):
            conexao.close()
            return "saldo insuficiente", 405
        else:
            try:
                saldo = saldo - valor
                cursor.execute(f"INSERT INTO transacoes (cliente_id, valor, tipo, descricao) VALUES ({id}, {valor}, '{tipo}', '{descricao}')")
                cursor.execute(f"UPDATE clientes SET saldo = {saldo} WHERE id = {id}")
                cursor.execute("COMMIT")
            except:
                cursor.execute("ROLLBACK")
                conexao.close()
                return "não foi possível acessar o banco de dados", 500
    elif tipo == "c":
        try:
            saldo = saldo + valor
            cursor.execute(f"INSERT INTO transacoes (cliente_id, valor, tipo, descricao) VALUES ({id}, {valor}, '{tipo}', '{descricao}')")
            cursor.execute(f"UPDATE clientes SET saldo = {saldo} WHERE id = {id}")
            cursor.execute("COMMIT")
        except:
                cursor.execute("ROLLBACK")
                conexao.close()
                return "não foi possível acessar o banco de dados", 500
   
    resultado = {
        "limite": limite,
        "saldo": saldo
    }
    conexao.close()
    return resultado, 200

    
@app.route("/clientes/<id>/extrato", methods=["GET"])
def extrato(id):
    conexao = pool.get_connection()
    cursor = conexao.cursor()
    try:
        cursor.execute(f"SELECT valor, tipo, descricao, data FROM transacoes WHERE cliente_id = {id} limit 10")
    except:
        conexao.close()
        return "não foi possível acessar o banco de dados", 500
    transacoes = cursor.fetchall()
    
    ultimas_transacoes = []
    for transacao in transacoes:
        ultima_transacao = {
            "valor": transacao[0],
            "tipo": transacao[1],
            "descricao": transacao[2],
            "realizada_em": transacao[3]
        }
        ultimas_transacoes.append(ultima_transacao)
        
    try:    
        cursor.execute(f"SELECT saldo, limite FROM clientes WHERE id = {id}")
    except:
        conexao.close()
        return "não foi possível acessar o banco de dados", 500
    dados = cursor.fetchall()
    
    extrato = {
        "saldo": {
            "total": dados[0][0],
            "data_extrato": datetime.now(),
            "limite": dados[0][1]
        },
        "ultimas_transacoes": ultimas_transacoes
    }
    
    conexao.close()
    return extrato, 200


if __name__ == "__main__":
    app.run(debug=True, port=5000, host="0.0.0.0")
