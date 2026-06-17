Estacionamento

Sistema de Estacionamento

Sobre o Projeto

O Sistema de Estacionamento é uma aplicação web desenvolvida em Python utilizando o framework Django. O objetivo do sistema é facilitar o gerenciamento de estacionamentos, permitindo o controle de entrada e saída de veículos, administração de vagas disponíveis, gerenciamento de usuários e cálculo automático de cobranças.

A aplicação foi desenvolvida com foco em organização, praticidade e automação dos processos de controle de veículos, oferecendo uma interface simples e intuitiva para os usuários.

Funcionalidades

Cadastro e autenticação de usuários;
Controle de entrada de veículos;
Controle de saída de veículos;
Cálculo automático do valor da permanência;
Gerenciamento de vagas disponíveis;
Painel administrativo para acompanhamento das movimentações;
Controle de permissões de usuários.
Tecnologias Utilizadas
Python
Django
SQLite
HTML5
CSS3
JavaScript
Como Executar o Projeto


## Como Executar o Projeto

### 1. Clone o repositório

```bash
git clone https://github.com/Jose-carlos504/Estacionamento.git
cd Estacionamento
Como Executar o Projeto
1. Clone o repositório
git clone https://github.com/Jose-carlos504/Estacionamento.git
cd Estacionamento
2. Crie um ambiente virtual (opcional, mas recomendado)
python -m venv venv
3. Ative o ambiente virtual
Windows

venv\Scripts\activate
Linux/Mac

source venv/bin/activate
4. Instale as dependências do projeto
pip install -r requirements.txt
O Django e as demais bibliotecas necessárias serão instalados automaticamente através do arquivo requirements.txt.

5. Execute as migrações do banco de dados
python manage.py migrate
6. Inicie o servidor
python manage.py runserver
7. Acesse o sistema
Abra o navegador e acesse:

http://127.0.0.1:8000/
Login das duas contas ja cadastradas:

login: cv senha: 123

login: admin123 senha: 123