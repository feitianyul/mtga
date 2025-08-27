# MTGA

<picture>
    <img alt="MTGA" src="https://github.com/BiFangKNT/mtga/blob/gui/icons/hero-img_f0bb32.png?raw=true">
</picture>

[![English](https://img.shields.io/badge/docs-English-purple)](README.en.md) [![简体中文](https://img.shields.io/badge/文档-简体中文-yellow)](../README.md) [![日本語](https://img.shields.io/badge/ドキュ-日本語-b7003a)](README.ja.md) [![한국어 문서](https://img.shields.io/badge/docs-한국어-green)](README.ko.md) [![Documentación en Español](https://img.shields.io/badge/docs-Español-orange)](README.es.md) [![Documentation en Français](https://img.shields.io/badge/docs-Français-blue)](README.fr.md) [![Documentação em Português (Brasil)](<https://img.shields.io/badge/docs-Português-purple>)](README.pt.md) [![Dokumentation auf Deutsch](https://img.shields.io/badge/docs-Deutsch-darkgreen)](README.de.md) [![Документация на русском языке](https://img.shields.io/badge/доки-Русский-darkblue)](README.ru.md)

## Introdução

MTGA é uma solução de provedor de serviços de modelo fixo para IDE baseada em proxy local, compatível com Windows e macOS.

**Nota: Atualmente, este projeto suporta apenas APIs no formato openai. Por favor, confirme. Outros formatos podem ser convertidos para o formato openai antes do uso.**

<details>
  <summary>Você não vê nada~~</summary>
  <br>
  <p>MTGA significa Make T Great Again!</p>
 </details>

## Índice

* [Registo de Alterações](#registo-de-alterações)
* [Início Rápido](#início-rápido)
  * [Utilizadores do Windows (Método de Inicialização com Um Clique via GUI)](#utilizadores-do-windows-método-de-inicialização-com-um-clique-via-gui)
  * [Utilizadores do macOS (Instalação de Aplicação)](#utilizadores-do-macos-instalação-de-aplicação)
* [Iniciar a Partir de Script](#iniciar-a-partir-de-script)
  * [Passo 0: Preparação do Ambiente](#passo-0-preparação-do-ambiente)
    * [Windows](#windows)
      * [Passo 1: Gerar Certificado Autoassinado](#passo-1-gerar-certificado-autoassinado)
      * [Passo 2: Fazer o Windows Confiar no Seu Certificado de AC](#passo-2-fazer-o-windows-confiar-no-seu-certificado-de-ac)
      * [Passo 3: Modificar o Ficheiro Hosts](#passo-3-modificar-o-ficheiro-hosts)
      * [Passo 4: Executar o Servidor Proxy Local (Python)](#passo-4-executar-o-servidor-proxy-local-python)
      * [Passo 5: Configurar o IDE Trae](#passo-5-configurar-o-ide-trae)
    * [macOS](#macos)
 * [😎 Manter-se Atualizado](#-manter-se-atualizado)

---

## Registo de Alterações

### v1.1.1 (Mais Recente)

- 🐛 **Corrigido problema na funcionalidade de modificação de hosts** - Resolvido problema de caracteres de nova linha anómalos ao modificar o ficheiro hosts

### v1.1.0

- ✨ **Nova funcionalidade de gestão de dados do utilizador** - Versão de ficheiro único suporta armazenamento persistente de dados do utilizador
  - Localização de armazenamento de dados: Windows `%APPDATA%\MTGA\`, macOS/Linux `~/.mtga/`
  - Suporta backup, restauro e limpeza de dados do utilizador
  - Ficheiro de configuração, certificado SSL, backup de hosts persistido automaticamente
- 🔧 **Otimizada construção de ficheiro único** - Melhorado `build_onefile.bat`, suporta variabilização do número de versão
- 🎯 **Interface do utilizador melhorada** - Adicionado botão de atualização da lista de grupos de configuração, layout da interface otimizado
- 📖 **Documentação aperfeiçoada** - Adicionado guia de construção de ficheiro único, documentação do projeto atualizada

### v1.0.0

- ✅ **Adaptação para Mac OS** - Suporte para instalação de aplicativos macOS  
- 🔄 **Alteração do provedor padrão** - Mudança de DeepSeek para OpenAI  
- 📦 **Refatoração de arquivos** - Arquivos relacionados a ds renomeados para o formato `*_ds.*` e arquivados  
- 🌐 **Alteração do formato da URL da API** - De `https://your-api.example.com/v1` para `https://your-api.example.com`

---

## Início Rápido

### Usuários do Windows (Método de inicialização com um clique via GUI)

1. Faça o download da versão mais recente de `MTGA_GUI-v{versão}-x64.exe` em [GitHub Releases](https://github.com/BiFangKNT/mtga/releases)  
2. Execute o arquivo exe baixado com um duplo clique (requer permissões de administrador)  
3. Na interface gráfica aberta, preencha a URL da API e o ID do modelo  
   - **A URL da API só precisa do domínio (a porta é opcional, se não souber, não preencha), não é necessário incluir a rota posterior, por exemplo: `https://your-api.example.com`**  
   - **Atenção para diferenciar o nome do modelo, não conflite com os nomes de modelos internos:**  
   - <img width="249" height="67" alt="differentiate model name" src="https://github.com/BiFangKNT/mtga/blob/gui/images/differentiate-model_name.png?raw=true" />  
4. Clique no botão "Iniciar Todos os Serviços com Um Clique"  
5. Aguarde até que o programa complete automaticamente as seguintes operações:  
   - Gerar e instalar o certificado  
   - Modificar o arquivo hosts  
   - Iniciar o servidor proxy  
6. Após a conclusão, configure o IDE de acordo com [Passo 5: Configurar o Trae IDE](#passo-5-configurar-o-trae-ide)

> **Nota:**  
> - A primeira execução pode exigir permissão de acesso ao firewall  
> - A versão de arquivo único suporta armazenamento persistente de dados do usuário, configurações e certificados são salvos automaticamente

### Usuários macOS (Instalação via aplicativo)

#### Método de instalação

1. Faça o download da versão mais recente de `MTGA_GUI-v{versão}-aarch64.dmg` em [GitHub Releases](https://github.com/BiFangKNT/mtga/releases)  
2. Clique duas vezes no arquivo DMG, o sistema montará automaticamente o pacote de instalação  
3. Arraste o `MTGA_GUI.app` para a pasta `Applications`  
4. Inicie o aplicativo a partir do Launchpad ou da pasta Applications

#### Como usar

1. Inicie o `MTGA_GUI.app` (na primeira execução, pode ser necessário permitir a execução nas Preferências do Sistema)
2. Preencha na interface gráfica:
   - **API URL**: Seu endereço de serviço de API (ex: `https://your-api.example.com`)
   - **ID do Modelo**: Nome personalizado do modelo (evite conflitos com modelos integrados)
3. Clique no botão "Iniciar Todos os Serviços com Um Clique"
4. O programa completará automaticamente:
   - Geração e instalação do certificado SSL no keychain do sistema
   - Modificação do arquivo `/etc/hosts` (requer permissões de administrador)
5. É necessário confiar manualmente no certificado gerado na janela do keychain aberta, com nome padrão `MyLocalCA`
6. Inicie o servidor proxy local
7. Complete a configuração conforme [Configuração do Trae IDE](#第-5-步配置-trae-ide) abaixo

> **Notas importantes:**
> - A primeira execução requer senha de administrador para modificar arquivos do sistema
> - Pode ser necessário permitir a execução do aplicativo em "Preferências do Sistema > Segurança e Privacidade"
> - Em caso de problemas de permissão de rede, permita o acesso do aplicativo em "Preferências do Sistema > Segurança e Privacidade > Firewall"

---

## Inicialização via Script

### Passo 0: Preparação do Ambiente

#### Windows

- Sistema Windows 10 ou superior
- Possuir permissões de administrador
- Instalar ambiente Python, recomendado Python 3.10 ou superior
- Instalar Git

##### Passo 1: Gerar Certificado Autoassinado

Abra o Git Bash:

```bash
# 切换到 ca 目录
cd "mtga/ca"

# 1. 生成 CA 证书 (ca.crt 和 ca.key)
./genca.sh
```

Ao executar `./genca.sh`, ele perguntará "Do you want to generate ca cert and key? [yes/no]", digite `y` e pressione Enter. Em seguida, solicitará algumas informações:

*   `Country Name (2 letter code) []`: Preencha `CN` (ou outro código de país)
*   Outros campos (como State, Locality, Organization, Common Name for CA) podem ser preenchidos conforme necessário ou deixados em branco, sugere-se preencher `X`. Common Name pode ser preenchido com `MyLocalCA` ou similar. E-mail pode ser deixado em branco.

```bash
# 2. 生成 api.openai.com 的服务器证书 (api.openai.com.crt 和 api.openai.com.key)
# 这个脚本会使用同目录下的 api.openai.com.subj 和 api.openai.com.cnf 配置文件
./gencrt.sh api.openai.com
```

Após a execução, no diretório `mtga\ca` você encontrará os seguintes arquivos importantes:

*   `ca.crt` (seu certificado CA personalizado)
*   `ca.key` (sua chave privada CA personalizada - **não compartilhe**)
*   `api.openai.com.crt` (certificado SSL para o servidor proxy local)
*   `api.openai.com.key` (chave privada SSL para o servidor proxy local - **não compartilhe**)

##### Passo 2: Fazer o Windows Confiar em Seu Certificado CA

1.  Localize o arquivo `mtga\ca\ca.crt`.
2.  Clique duplo no arquivo `ca.crt` para abrir o visualizador de certificados.
3.  Clique no botão "Instalar Certificado...".
4.  Selecione "Usuário Atual" ou "Computador Local". Recomenda-se selecionar "Computador Local" (requer permissões de administrador) para aplicar a todos os usuários.
5.  Na próxima caixa de diálogo, selecione "Colocar todos os certificados no seguinte repositório" e clique em "Procurar...".
6.  Selecione "Autoridades de Certificação Raiz Confiáveis" e clique em "OK".
7.  Clique em "Avançar" e depois "Concluir". Se aparecer um aviso de segurança, selecione "Sim".

##### Passo 3: Modificar Arquivo Hosts

**⚠️ AVISO: Após executar este passo, você não conseguirá mais acessar a API original da OpenAI. O uso via navegador não é afetado.**

Você precisa modificar o arquivo Hosts com permissões de administrador, apontando `api.openai.com` para sua máquina local.

1.  Caminho do arquivo Hosts: `C:\Windows\System32\drivers\etc\hosts`
2.  Abra este arquivo como administrador, usando o Bloco de Notas (ou outro editor de texto).
3.  Adicione a seguinte linha no final do arquivo:
    ```
    127.0.0.1 api.openai.com
    ```
4.  Salve o arquivo.

##### Passo 4: Executar o servidor proxy local (Python)

**Antes de executar o servidor proxy:**

1.  **Instalar dependências**:
    ```bash
    pip install Flask requests
    ```
2.  **Configurar o script**:
    *   Abra o arquivo `trae_proxy.py`.
    *   **Modifique `TARGET_API_BASE_URL`**: Substitua pela URL base real da API no formato OpenAI do site ao qual você deseja se conectar (por exemplo: `"https://your-api.example.com"`).
    *   **Confirme o caminho do certificado**: O script, por padrão, lerá `api.openai.com.crt` e `api.openai.com.key` de `mtga\ca`. Se seus certificados não estiverem nesse caminho, modifique os valores de `CERT_FILE` e `KEY_FILE`, ou copie esses dois arquivos para o `CERT_DIR` especificado no script.

**Executar o servidor proxy:**

Abra o Prompt de Comando (cmd) ou PowerShell **executando como administrador** (porque precisa escutar na porta 443) e execute:

```bash
python trae_proxy.py
```

Se tudo correr bem, você deverá ver os logs de inicialização do servidor.

##### Passo 5: Configurar o Trae IDE

1.  Abra e faça login no Trae IDE.
2.  No diálogo de IA, clique no ícone do modelo no canto inferior direito e selecione "Adicionar modelo" no final.
3.  **Provedor**: Selecione `OpenAI`.
4.  **Modelo**: Selecione "Modelo personalizado".
5.  **ID do Modelo**: Preencha com o valor que você definiu para `CUSTOM_MODEL_ID` no script Python (por exemplo: `my-custom-local-model`).
6.  **Chave da API**:
    *   Se sua API de destino requer uma chave de API e o Trae a enviará via `Authorization: Bearer <chave>`, então a chave preenchida aqui será encaminhada pelo proxy Python.
    *   Ao configurar a OpenAI no Trae, a chave da API está relacionada à configuração `remove_reasoning_content`. Nosso proxy Python não processa essa lógica, ele apenas encaminha o cabeçalho Authorization. Você pode tentar preencher com a chave necessária para sua API de destino, ou com uma chave arbitrária no formato `sk-xxxx`.

7.  Clique em "Adicionar modelo".
8.  Volte à caixa de chat de IA e selecione o modelo personalizado que você acabou de adicionar no canto inferior direito.

Agora, quando você interagir com este modelo personalizado através do Trae, as solicitações devem passar pelo seu proxy Python local e serem encaminhadas para o `TARGET_API_BASE_URL` que você configurou.

**Dicas para Resolução de Problemas:**

*   **Conflito de Portas**: Se a porta 443 já estiver em uso (por exemplo, por IIS, Skype ou outros serviços), o script Python falhará ao iniciar. Você precisa parar o serviço que está usando a porta ou modificar o script Python e o Nginx (se estiver usando) para escutar em uma porta diferente (mas isso é mais complexo, pois o Trae tem o acesso à porta 443 de `https://api.openai.com` codificado).
*   **Firewall**: Certifique-se de que o firewall do Windows permite conexões de entrada na porta 443 para o Python (embora seja uma conexão local `127.0.0.1` e geralmente não exija configuração especial de firewall, vale a pena verificar).
*   **Problemas de Certificado**: Se o Trae relatar erros relacionados a SSL/TLS, verifique cuidadosamente se o certificado CA foi instalado corretamente nas "Autoridades de Certificação Raiz Confiáveis" e se o proxy Python carregou corretamente os arquivos `api.openai.com.crt` e `.key`.
*   **Logs do Proxy**: O script Python imprimirá alguns logs que podem ajudá-lo a diagnosticar problemas.

Esta solução é mais integrada do que usar diretamente vproxy + nginx, colocando a finalização TLS e a lógica de proxy em um único script Python, sendo mais adequada para validação rápida de protótipos no Windows.

#### macOS

-> [Método de Inicialização via Script para Mac OS](https://github.com/BiFangKNT/mtga/blob/gui/docs/README_macOS_cli.md)

---

## 😎 Mantenha-se Atualizado

Clique em Star e Watch no canto superior direito do repositório para obter as atualizações mais recentes.

![star to keep latest](https://github.com/BiFangKNT/mtga/blob/gui/images/star-to-keep-latest.gif?raw=true)

---

## Referências

O diretório `ca` é referenciado do repositório `wkgcass/vproxy`, agradecimentos ao grande mestre!