
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY,
    nome VARCHAR(50) NOT NULL,
    limite INTEGER NOT NULL,
    saldo INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS transacoes (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER NOT NULL,
    valor INTEGER NOT NULL,
    tipo VARCHAR(1) NOT NULL,
    descricao VARCHAR(10) NOT NULL,
    data TIMESTAMP NOT NULL DEFAULT NOW(),
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
);

CREATE INDEX idx_cliente_id ON transacoes (cliente_id);

INSERT INTO clientes (id, nome, limite, saldo) 
VALUES 
    (1, 'o barato sai caro', 100000, 0),
    (2, 'zan corp ltda', 80000, 0),
    (3, 'les cruders', 1000000, 0),
    (4, 'padaria joia de cocaia', 10000000, 0),
    (5, 'kid mais', 500000, 0);


