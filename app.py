from datetime import datetime
from flask import Flask,  request
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
    parametros = request.json
    app.logger.debug(parametros)
    
    try:
        valor = int(parametros["valor"])
    except:
        app.logger.debug("valor deve ser um número inteiro")
        return "valor deve ser um número inteiro", 422   
    tipo = parametros["tipo"]
    if tipo not in ["c", "d"]:
        app.logger.debug("tipo deve ser c ou d")
        return "tipo deve ser c ou d", 422
    descricao = parametros["descricao"]
    if len(descricao) > 10:
        app.logger.debug("descrição deve ter no máximo 10 caracteres")
        return "descrição deve ter no máximo 10 caracteres", 422
    
    conexao = pool.get_connection()
    cursor = conexao.cursor()
    try:
        cursor.execute(f"SELECT saldo, limite FROM clientes WHERE id = {id}")
    except:
        conexao.close()
        app.logger.debug("erro transacoes dados")
        return "não foi possível acessar o banco de dados", 500
    dados = cursor.fetchall()
    if not dados:
        conexao.close()
        app.logger.debug("id não existente")
        return "id não existente", 404
    
    saldo = dados[0][0]
    limite = dados[0][1]
    
    if tipo == "d":
        if saldo - valor < (-limite):
            conexao.close()
            app.logger.debug("saldo insuficiente")
            return "saldo insuficiente", 422
        else:
            try:
                saldo = saldo - valor
                cursor.execute(f"INSERT INTO transacoes (cliente_id, valor, tipo, descricao) VALUES ({id}, {valor}, '{tipo}', '{descricao}')")
                cursor.execute(f"UPDATE clientes SET saldo = {saldo} WHERE id = {id}")
                cursor.execute("COMMIT")
            except:
                cursor.execute("ROLLBACK")
                conexao.close()
                app.logger.debug("erro transacoes d")
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
                app.logger.debug("erro transacoes c")
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
        app.logger.debug("erro extrato transacoes")
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
        app.logger.debug("erro extrato clientes")
        return "não foi possível acessar o banco de dados", 500
    
    dados = cursor.fetchall()
    if not dados:
        conexao.close()
        app.logger.debug("id não existente")
        return "id não existente", 404
    
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
