# ✦ ASTRO

[Español](README.md) · [English](README.md#in-english) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Italiano](README.it.md) · **Português**

**O seu assistente para as noites de astrofotografia.**

Quem faz fotografia de céu profundo conhece bem a cena: regressa de uma noite de captura com centenas de exposições e tem de as rever uma a uma. Em quais estão as estrelas tremidas? Em quais passou um satélite ou entrou uma nuvem? Tenho os darks e os flats de que preciso para esta sessão?

O ASTRO faz esse trabalho por si. É gratuito, funciona em **Mac** e em **Windows**, está disponível em **espanhol**, **inglês**, **francês**, **alemão**, **italiano** e **português**, e tem três aspetos: **Dia**, **Noite** e **Vermelho**, este último para usar junto ao telescópio sem perder a adaptação à escuridão.

---

## O que faz?

**Revê os seus lights.** Mede as estrelas de cada exposição e indica quais estão bem, quais têm algum problema e quais convém descartar: estrelas alongadas, desfocagem, rastos de satélites ou aviões, nuvens ou um fundo demasiado brilhante. E explica o motivo em linguagem simples. Se o seu equipamento ou o seu céu não permitem tanto, com o **critério de qualidade** ajusta-se com um cursor o grau de exigência da avaliação, ou fica-se só com os melhores X % de cada filtro, vendo no momento quantas exposições passam e qual é a primeira que fica de fora. Se o cabeçalho não traz o objeto, o filtro, o telescópio ou a câmara (ou os traz errados), é possível alterá-los em muitas exposições de uma só vez. Cada exposição tem também os indicadores do SubframeSelector do PixInsight (nitidez, redondeza, estrelas, fundo, ruído e SNR), com gráficos por sessão ou de todo o projeto, e pode dar a cada projeto os seus próprios limites para deixar de fora o que não chega. E com o **blink** passa as exposições uma após outra, alinhadas pelas suas estrelas, para apanhar de relance um satélite, um véu de nuvens ou estrelas arrastadas, e deixa-as fora do empilhamento ou descarta-as com uma tecla.

**Vigia a noite por si.** Com «Em direto», o ASTRO observa a pasta onde a ASIAIR (pela rede) ou o N.I.N.A. vão guardando as fotos e revê cada exposição assim que termina. Se entrarem nuvens, as estrelas se alongarem, a focagem se perder ou a sequência parar, avisa com um som e uma notificação, e mostra em gráficos como está a correr a noite. Pode ficar no sofá sem ter de sair a toda a hora para ver. E pode acompanhar tudo **a partir do telemóvel**: basta ler um código QR para ver nele as últimas exposições, o gráfico e os avisos, com som, vibração e modo vermelho.

**Diz-lhe se compensa continuar com um filtro.** O ASTRO empilha uma parte e a totalidade das suas exposições de cada filtro e mede se o sinal fraco e o detalhe continuam a crescer ou se já chegou ao limite, quantas horas mais seriam precisas para notar a diferença e que canal de cor está mais fraco.

**Explica porque correu mal uma exposição.** Dê-lhe os registos da ASIAIR (o da sessão e o da guiagem do PHD2) e o ASTRO liga cada exposição ao que estava a acontecer nesse momento: o RMS da guiagem, se estabilizou após o *dither*, a última focagem, a inversão no meridiano. Além disso, resume os problemas de cada noite: uma centragem que se afasta após a inversão, exposições feitas sem seguimento ou uma guiagem que se descontrola depois de refocar. E se o seu programa de captura guardar a posição do focador (N.I.N.A., SGP, KStars…), «Focagem por filtro» calcula o desvio de cada filtro e quanto se move a focagem com a temperatura.

**Organiza a sua biblioteca de calibração.** Guarda os seus bias, darks e flats, avalia-os e avisa do que falta. Com um botão, indica que exposições de calibração tem de fazer para cada objeto e prepara a lista para a ASIAIR ou uma sequência pronta a carregar no N.I.N.A.

**Dá conta das suas sessões sozinho.** Indique-lhe uma vez em que pastas a ASIAIR, o N.I.N.A. ou o seu programa de captura guardam as fotos, e o ASTRO revê-as ao abrir e a cada dez minutos: as exposições novas são analisadas e arrumadas automaticamente, sem arrastar nada.

**Põe ordem em anos de fotografias.** A secção **Arquivo** indexa as suas pastas de todos os anos lendo só os cabeçalhos, sem copiar nada, e mostra-lhe cada projeto com as suas horas por filtro e por temporada, o seu estado (em curso, empilhado, por voltar a empilhar, terminado ou em pausa), as suas sessões e os equipamentos usados. Dentro de cada um, analisa-o, depura-o e empilha-o passo a passo. Os darks e flats que encontrar nas suas pastas passam com um clique para a biblioteca de calibração, vê que dark e que flat cabe a cada noite, e avisa se numa temporada a câmara estava rodada ou o enquadramento deslocado. Se um objeto tiver dois nomes (M31, Andrómeda), reconhece-o pelas coordenadas e propõe juntá-los. **Resolve com o Siril** a melhor exposição de cada noite e leva a astrometria às outras pelas estrelas (centro, ângulo e escala reais), guarda o **histórico** de cada projeto (noites, empilhamentos, limites, mudanças de calibração e de estado) e desenha-os todos num **mapa do céu** com o seu campo.

**Ajuda a chegar ao seu objetivo.** Para cada objeto, vê quantas horas úteis já tem por filtro, quantas faltam e, mais ou menos, de quantas noites mais vai precisar. E como evolui noite a noite: o FWHM e o fundo de cada sessão, que noites foram fracas (em comparação com o normal de cada equipamento e filtro) e quanto melhora realmente a relação sinal/ruído com mais uma noite. As noites fracas podem **ficar fora do empilhamento** com um botão, sem apagar nada, e na ficha de cada exposição vê **que dark, flat e bias lhe correspondem** ao empilhar e o que lhe falta.

**E diz-lhe quando.** Com o seu local de observação, a Lua e a altura de cada objeto, o ASTRO mostra que noites do próximo mês servem para o que falta: a banda larga quando não há Lua e o Hα, o OIII ou o SII quando há. Em «Próximas noites» vê num relance o que fazer esta noite e nas seguintes, com a previsão dos próximos sete dias hora a hora (nuvens, humidade, orvalho e vento). Guarda vários locais, cada um com o seu horizonte (as árvores, a casa ou a cúpula), e desenha a altura de cada objeto esta noite. Também lhe diz quando se vê o núcleo da Via Láctea e avisa se a Estação Espacial ou outro satélite brilhante vai atravessar o campo do seu objeto esta noite. E se procura algo novo, **«O que fotografar?»** propõe objetos que cabem no campo do seu equipamento e prepara o plano para o N.I.N.A. ou para a ASIAIR.

**Diz-lhe o que montar esta noite.** Em «O meu equipamento» regista as suas peças soltas: telescópios, redutores, câmaras e filtros. Em cada noite, o ASTRO experimenta todas as combinações e propõe um plano: que objeto, **que telescópio com que câmara** (a que melhor o enquadra e amostra), **por qual dos seus filtros começar** conforme a Lua e **que tempo de exposição usar com o seu céu** (com o SQM ou o Bortle do seu local). Se uma noite não chegar, propõe um **projeto** com as horas que convém reunir e vai somando o que captar. E envia-lhe tudo **por WhatsApp**: com um botão, ou automaticamente todas as tardes à hora que escolher. O plano também sai **como sequência para o N.I.N.A.** ou como lista para copiar para a **ASIAIR**, e na manhã seguinte recebe o **resumo da noite**: quantas exposições valem, as horas por filtro, como vai o projeto e que calibração falta.

**Projetos em grupo.** Se o fizerem entre vários sócios, partilham uma pasta (Google Drive, Dropbox, OneDrive ou um disco de rede): cada um deixa as suas exposições na pasta do seu equipamento e o ASTRO de todos junta-as automaticamente no mesmo projeto, com a ficha e o contributo de cada equipamento.

**Os seus dados não ficam presos.** Cada objeto pode ser exportado como um projeto num ZIP com formatos abertos (JSON e CSV que se abrem no Excel), com a avaliação de cada exposição e a calibração que lhe corresponde e, se quiser, também as exposições, os darks, flats e bias e os empilhamentos. Serve para o arquivar, passá-lo a um colega ou continuar com ele noutro computador ou noutro programa; e volta a ser importado no ASTRO sem duplicar nada.

**Empilha por si.** Se tiver o Siril instalado (também gratuito), o ASTRO empilha cada objeto por filtros usando as calibrações correspondentes. Cada exposição conta segundo o seu ruído, como no PixInsight: as de melhor sinal pesam mais. Se fotografou o mesmo objeto com vários telescópios ou câmaras (ou com a mesma câmara em telescópios diferentes, que distingue pela escala), empilha cada equipamento separadamente e depois combina-os numa escala e num enquadramento comuns, e mostra no resumo do objeto quanto já tem com cada um. A partir da janela inicial pode criar um **projeto com vários equipamentos**, seus ou de colegas: cada equipamento tem a sua ficha com todos os seus valores (câmara, rotador, filtros, o contributo para o projeto) e recomendações para tirar mais partido dele.

**E mede com as suas fotos.** A secção **Ciência** transforma as suas exposições em medições: o **brilho do seu céu** em magnitudes por segundo de arco quadrado (o mesmo que um SQM, mas na direção exata do telescópio), a **magnitude limite** de cada exposição ou empilhamento, o tamanho das estrelas e a transparência da noite, calibrado com as estrelas do catálogo **Gaia**. Guarda a série noite a noite e local a local, e cada medição sai com o seu **pacote de rastreabilidade** (método, catálogo, script do Siril e impressões digitais dos ficheiros) para a poder usar num relatório ou num artigo. E mede **estrelas variáveis** para a **AAVSO**: descarrega a sequência oficial de comparação, mede cada exposição, desenha a curva de luz e deixa o relatório no formato AAVSO Extended pronto a enviar para o WebObs. E mede **trânsitos de exoplanetas** para o **ExoClock**: indica que trânsitos são visíveis a partir do seu local nas próximas noites, escolhe as estrelas de comparação do Gaia, ajusta o trânsito e dá o instante central em BJD_TDB com o seu erro e o O−C, com a curva pronta a enviar. E cronometra o **máximo das RR Lyrae** para o **GEOS**: indica que máximos são visíveis a partir do seu local nas próximas noites, procura os elementos da estrela no VSX, ajusta o máximo e dá o seu instante em HJD com o seu erro e o O−C, com o ficheiro pronto para a base de dados de RR Lyrae. E faz **astrometria de asteroides e cometas**: pergunta ao JPL que objetos há no seu campo, mede a sua posição com as estrelas do Gaia, compara-a com a efeméride e prepara o relatório **ADES** para o Minor Planet Center. E desenha o **diagrama H-R de um enxame**: com dois empilhamentos (azul e verde) mede todas as estrelas, encontra os membros com o Gaia e calcula a sua distância e o seu avermelhamento. E faz **espetroscopia** com uma rede de difração à frente da câmara (tipo Star Analyser): extrai o espetro, calibra-o com as linhas do hidrogénio e do ar, mede as linhas e guarda-o em FITS para o ISIS ou o VSpec. E, como faixa bónus, **Cem ligações do céu**: os cem sites de astronomia e astrofotografia que vale a pena ter à mão, com uma linha sobre cada um.

**E mostra o resultado.** No fim, o ASTRO revela a imagem por si: remove o gradiente do fundo, equilibra a cor e estica o histograma e, se tiver os filtros, monta também as versões RGB, LRGB, SHO (a paleta Hubble) ou HOO. Nada de abrir um ficheiro negro sem saber se ficou bem: vê-o no momento. E quando a quiser finalizar, um botão abre-a diretamente no GIMP, no Photoshop, no PixInsight ou no programa que usar.

---

## Como começar

1. Entre em **[Releases](../../releases/latest)** e descarregue o ficheiro do seu computador:
   - Mac com chip Apple (M1, M2, M3, M4…): **ASTRO-Mac-AppleSilicon.zip**
   - Mac com processador Intel: **ASTRO-Mac-Intel.zip**
   - Windows 10 ou 11: **ASTRO-Windows.exe**
2. **Faça duplo clique.** O ASTRO instala-se sozinho e, a partir daí, atualiza-se sozinho (e mostra-lhe as novidades de cada versão).
3. Escolha o idioma e a pasta onde quer guardar as suas fotos. Pode estar num disco externo. Prefere espreitar primeiro? Clique em **«Ver com dados de exemplo»** e explore-o com exposições e medidas de exemplo, sem mexer em nada seu.
4. Na **janela inicial**, escolha por onde começar: cada secção (Adicionar exposições, Os meus objetos, Arquivo, Vários equipamentos, Empilhar com o Siril, Próximas noites, O que fotografar?, Sessão em direto, Calibração e Ciência) tem o seu desenho e abre-se na mesma janela do ASTRO, sem navegador; «Todas as secções», em cima à esquerda, leva-o de volta ao início. Arraste a pasta de uma noite de fotos e deixe o ASTRO fazer o resto.

No **Mac**, o ASTRO está assinado e aprovado pela Apple: abre-se com um duplo clique, sem avisos.

No **Windows**, da primeira vez o seu computador vai avisar que o programa não está assinado (é normal em programas gratuitos feitos por amadores): clique em *Mais informações → Executar mesmo assim*. Não volta a aparecer.

---

## As suas fotos são suas

O ASTRO trabalha no seu computador. **Não envia nada para a Internet**: apenas verifica de vez em quando se há uma versão nova e, se usar «Próximas noites», pede a previsão do tempo da sua zona ao Open-Meteo.com enviando apenas a sua posição aproximada (pode ser desativado); para o plano desta noite descarrega uma vez por dia as órbitas dos satélites brilhantes do CelesTrak.org (sem enviar nada); em «O que fotografar?» mostra imagens do céu do serviço CDS de Estrasburgo e, em «Ciência», consulta o catálogo Gaia (na ESA ou no CDS) enviando apenas as coordenadas do campo que mede e, para as estrelas variáveis, o nome da estrela à AAVSO (VSX e VSP), nunca as suas fotos; para os trânsitos, descarrega a lista de planetas do ExoClock e do arquivo de exoplanetas da NASA; para as RR Lyrae, a lista de RR Lyrae do VSX (através do VizieR, no CDS) e os dados da estrela que mede, e para os asteroides consulta o JPL com o centro do campo, a hora e as coordenadas do seu local. Se ativar o WhatsApp automático, a mensagem de cada tarde é enviada através do CallMeBot, um serviço gratuito de terceiros. Copia as suas exposições para a sua pasta sem tocar nos originais ou, se preferir, analisa-as e empilha-as a partir de onde estão, sem as copiar.

---

## Esta é uma versão de teste

O ASTRO está em **beta**, por isso pode ter alguma falha. Se encontrar algo estranho, ou sentir falta de alguma coisa, conte-me a partir do próprio programa: **Mais opções → Comunicar um problema ou sugestão**. Tudo ajuda, incluindo saber do que gosta.

Se vai testá-lo, dê uma vista de olhos ao **[guia para testadores](GUIA-BETA.pt.md)**.

---

## Quem está por trás

O ASTRO foi criado por **Tomás Moreno González**, astrofotógrafo e divulgador, membro de **Astrocitas**, da **Asociación Astronómica Azarquiel (Piedrabuena, C.Real)** e da **Agrupación Astronómica de Miguelturra (C.Real)**.

<p align="center">
  <img src="imagenes/web/escudo-astrocitas.png" height="80" alt="Astrocitas">&nbsp;&nbsp;&nbsp;
  <img src="imagenes/web/escudo-azarquiel.png" height="118" alt="Asociación Astronómica Azarquiel (Piedrabuena, C.Real)">&nbsp;&nbsp;&nbsp;
  <img src="imagenes/web/escudo-miguelturra.png" height="80" alt="Agrupación Astronómica de Miguelturra (C.Real)">
</p>

Nasceu de uma necessidade muito concreta: passar menos tempo a rever fotos e mais tempo a olhar para o céu.

Quer saber mais sobre como está feito ou como publicar versões novas? Está tudo no **[LEEME.pt.md](LEEME.pt.md)**.

---

## Apoiar o ASTRO

O ASTRO é gratuito. Se lhe for útil, pode ajudar a que continue a crescer com um donativo: **[Doar com PayPal](https://paypal.me/tmg197210)**. O botão também está na janela inicial do ASTRO e em «Acerca do ASTRO».
