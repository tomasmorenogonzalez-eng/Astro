# ✦ ASTRO beta · Guia para testadores

[Español](GUIA-BETA.md) · [English](GUIA-BETA.md#-astro-beta--tester-guide) · [Français](GUIA-BETA.fr.md) · [Deutsch](GUIA-BETA.de.md) · [Italiano](GUIA-BETA.it.md) · **Português**

Obrigado por testar o ASTRO! É uma **versão de teste**: pode ter falhas, e é precisamente para as encontrar que preciso da sua ajuda.

## O que é o ASTRO
Um programa gratuito de astrofotografia que:
- **revê os seus lights**: mede as estrelas (FWHM e alongamento) e deteta rastos de satélites, nuvens e desfocagem;
- **vigia a noite em direto**: revê cada exposição à medida que a ASIAIR ou o N.I.N.A. a fazem e avisa se algo corre mal;
- **organiza a sua biblioteca de calibração** (bias, darks, flats) e diz **o que lhe falta**, com a lista para a ASIAIR ou uma **sequência pronta para o N.I.N.A.**;
- **empilha** cada objeto por filtros e deixa uma **pré-visualização já revelada** (e as combinações RGB, LRGB, SHO ou HOO), pronta a abrir no GIMP, no Photoshop ou no PixInsight.

Funciona em **Mac** e **Windows**, em espanhol, inglês, francês, alemão, italiano e português.

## Instalação (2 minutos)
1. Descarregue o ficheiro do seu computador a partir da página de transferências (**Releases**).
2. **Faça duplo clique.** O ASTRO instala-se sozinho e atualiza-se sozinho quando houver versões novas.
3. O aviso de segurança:
   - **Mac:** nenhum: o ASTRO está assinado e aprovado pela Apple. (Se mesmo assim o Mac avisar: *Definições do Sistema → Privacidade e segurança → «Abrir mesmo assim»*.)
   - **Windows:** só da primeira vez, o sistema avisa que o programa não está assinado: *Mais informações → Executar mesmo assim*.
4. Quer espreitar antes de usar as suas fotografias? Na primeira janela, clique em **«Ver com dados de exemplo»**.
5. Instale o **Siril** a partir de siril.org se quiser empilhar.

## O que peço que teste
Use o ASTRO com **os seus dados reais**, como faria normalmente. Se tiver tempo, estas são as partes que mais me interessa verificar:

1. **Adicionar uma sessão** de lights: as avaliações (válida / com avisos / a rejeitar) coincidem com o que vê nas exposições? Experimente também **«De uma pasta do disco»** com «Só analisar»: o ASTRO segue as ligações simbólicas e depois pode empilhar as exposições sem as ter copiado.
2. **O seu equipamento:** reconhece bem a sua câmara, telescópio, filtros, exposição e temperatura?
3. **Biblioteca de calibração:** adicione darks, flats e bias, ou importe-os da **ASIAIR** ou do **N.I.N.A.**
4. **«O que me falta?»**: acerta no que lhe falta? Se usa o N.I.N.A., experimente carregar a sequência que gera.
5. **Empilhar** um objeto. A **pré-visualização** parece razoável? «Abrir com…» encontra os seus programas de edição?
6. A **página de um projeto** (o objetivo de horas, «Preciso de mais horas?» e «Quando fazê-lo») e **«Planear sessão»** (a janela «Próximas noites»): as noites que propõe para cada filtro fazem sentido com a Lua que vê?
7. **«Em direto»** durante uma noite de captura, com a ASIAIR pela rede ou com o N.I.N.A.: encontra a pasta? Chegam os avisos (som e notificação) quando entra uma nuvem ou a sequência para? Há algum aviso a mais, ou algum de que sinta falta?
8. **«Explorar objetos»** (a janela «O que fotografar?») e os **locais com horizonte**: propõe objetos que façam sentido para o seu equipamento? Se usa o N.I.N.A., experimente carregar o plano que guarda.
9. **Pastas vigiadas**: em «Adicionar exposições», vigie a pasta onde guarda as exposições e verifique que, ao abrir o ASTRO, as sessões novas aparecem sozinhas. E na página de um projeto com várias noites, no passo «Qualidade», veja **«Como evolui, noite a noite»**: as noites fracas coincidem com o que se lembra?
10. **«O meu equipamento» e o plano da noite**: registe os seus telescópios, câmaras e filtros. Faz sentido o que propõe montar, o filtro e o tempo por exposição para o seu céu? Crie um projeto e experimente o WhatsApp (o botão e, se quiser, o envio automático de todas as tardes).
11. **Ciência → Magnitude limite e qualidade do céu**: meça algumas exposições de uma noite (de preferência com darks e flats na biblioteca). O brilho do céu parece-se com o do seu SQM ou com o que espera do seu local? A magnitude limite faz sentido para o seu equipamento? O Siril precisa de Internet da primeira vez para resolver cada campo (ou do seu catálogo local do Gaia).
12. **Ciência → Estrelas variáveis**: se tiver uma série de exposições de uma variável (uma noite, mesmo filtro), meça-a. Encontra a estrela e a sua sequência da AAVSO? A curva de luz parece-se com o esperado (ou com a da AAVSO dessa noite)? A estrela de controlo sai plana? Se tiver código de observador, veja se o WebObs aceita o ficheiro sem erros.
13. **Ciência → Exoplanetas**: veja que trânsitos propõe para as próximas noites a partir do seu local. Se tiver (ou captar) um trânsito, meça-o: o instante central e o O−C parecem-se com o que dão o HOPS, o EXOTIC ou o AstroImageJ com as mesmas exposições? O ExoClock aceita a curva?
14. **Ciência → RR Lyrae**: procure os máximos das próximas noites a partir do seu local. Se captar um (cerca de três horas seguidas em torno do máximo), meça-o: o instante coincide com o do Peranso ou do AstroImageJ com as mesmas exposições? E o O−C com o da estrela na base de dados do GEOS?
15. **Ciência → Asteroides e cometas**: meça um campo com algum asteroide (três ou mais exposições separadas por alguns minutos). Encontra os asteroides conhecidos? O O−C fica abaixo de um segundo de arco? O relatório ADES é validado na página de teste do MPC?
16. **Ciência → Diagramas H-R**: se tiver empilhamentos de um enxame aberto em dois filtros (ou a cores), meça-o. A distância e o avermelhamento parecem-se com os publicados (por exemplo, no WEBDA ou em Cantat-Gaudin 2020)?
17. **Ciência → Espetroscopia**: se tiver um Star Analyser, meça o espetro de uma estrela brilhante (Vega é ideal). Encontra a estrela e o espetro? As linhas de Balmer caem no sítio certo? Se medir outra estrela na mesma noite, experimente usar Vega como referência.
18. **O novo aspeto**: experimente os modos Dia, Noite e Vermelho (em baixo, à esquerda). Lê-se tudo bem? Há algo no modo Vermelho que o incomode à noite?
19. **O meu arquivo → Indexar pastas**: se tem anos de fotografias em pastas, clique em «Indexar uma pasta» e escolha a pasta principal. Quanto tempo demora? Os seus projetos, as horas por filtro e as temporadas estão certos? Entre num projeto e siga os passos (Exposições, Analisar, Qualidade, Empilhamento e Processamento). Falta-lhe alguma coisa para continuar os seus projetos ano após ano?
20. **Dados de exemplo e novidades**: experimente «Ver com dados de exemplo» (na primeira janela) e dê uma volta por todas as secções. Percebe-se o que faz cada uma? Volta bem aos seus dados com «Usar os meus dados» (o aviso amarelo à esquerda)? E quando o ASTRO se atualizou, apareceu a janela «Novidades»?
21. **Estados e indicadores de qualidade**: em Projetos, veja o estado dos seus, dê algum por capturado e experimente os separadores «Sessões» e «Equipamentos» de «O meu arquivo → Indexar pastas». Abra «Indicadores de qualidade» (em O meu arquivo) com uma sessão sua: as exposições que ficam fora das linhas de aviso e de rejeição são as que você descartaria? Se as suas exposições vêm de uma versão anterior, clique primeiro em «Medir esta sessão». Em cada projeto, veja o **Enquadramento**: deteta bem as temporadas em que rodou a câmara ou mudou de redutor? E se ao indexar aparecem darks ou flats, experimente «Adicioná-los à biblioteca»: classifica-os bem por câmara?
22. **Limites, pesos e calibração**: num projeto com muitas noites, abra «Indicadores e limites do projeto». Vê de relance que noites foram piores? Ponha um limite de FWHM ou de peso: as exposições que deixa de fora são as que tiraria? Empilhe com «Dar mais peso às exposições com melhor sinal» e compare com um empilhamento sem pesos: nota-se? E no passo «Empilhamento», carregue em «O que calibra cada noite»: bate certo com os darks e flats que usaria?
23. **A janela do ASTRO**: agora tudo se abre na sua própria janela, sem navegador. Passe de uma secção para outra com a barra da esquerda (a janela inicial continua em «Definições → Geral → Janela inicial…»). É mais cómodo? Sente falta de alguma coisa do navegador? Se algo não aparecer ou não responder, experimente «Usar o navegador em vez desta janela» e conte-me o que acontecia.
24. **As novidades da 0.27**: passe as exposições de uma noite com o **Blink** (em «Todas as exposições», num projeto ou na ficha de uma exposição): alinham-se bem, também depois da inversão no meridiano? Apanha algum satélite ou nuvem que a análise não assinalou? No Enquadramento de um projeto, clique em **«Resolver com o ASTRO»**: o centro, o ângulo e a escala coincidem com os do seu programa de captura? Veja o **Mapa do céu** (na Visão geral) e o **Histórico** de um projeto. Se tiver um objeto com dois nomes (M31 e Andrómeda), propõe juntá-los em «Nomes de objeto»? E se usar a mesma câmara em dois telescópios, separa-os?
25. **As novidades da 0.28**: na **Ciência**, abra a faixa bónus **Cem ligações do céu**: a pesquisa e os filtros funcionam? Falta algum site ou há algum a mais? Os cartões leem-se bem sobre as fotos de fundo, com os aspetos Dia, Noite e Vermelho?
26. **As novidades da 0.30**: o ASTRO abre-se na **Visão geral**. Veja «Esta noite», os seus projetos em curso e **«As suas noites»** (por ano e mês, em noites ou em horas, com os filtros de local, equipamento e objeto): os números batem certo com o que se lembra? Em **Projetos**, experimente os cinco estados (Novo, Em curso, Capturado, Processado e Arquivado), a pesquisa («Andrómeda» encontra M 31?), os cartões e a tabela, e o aviso dos projetos sem exposições novas há mais de um ano (com «Anular»). Abra um projeto: «Preciso de mais horas?» diz o que espera quando define um objetivo de 10, 20 ou 40 h? Em **Processamento**, registe a imagem final (TIF, PNG ou JPG) e onde a partilhou: abrem-se bem o ficheiro e as ligações? E as janelas: o Esc fecha a de cima, o clique fora fecha as de consulta e o «← Voltar» leva-o à anterior? Vê-se bem num ecrã pequeno ou no telemóvel?
27. **Novidade da 0.31**: se fotografa de mais de um sítio, abra **Definições → Locais de observação**: o ASTRO reparte bem as suas exposições por local (pelas coordenadas do cabeçalho)? Se usa a ASIAIR (que não as escreve), experimente **«Definir o local de cada noite…»** e veja a tabela **«Por local»** na página de um projeto: as horas e as noites de cada sítio batem certo? Empilhe um objeto escolhendo um só local. De que sente falta se viajar com o seu equipamento? Experimente também **«Compor canais…»** (página do projeto → passo «Processamento») com os seus filtros (LRGB, RGB, SHO, HOO ou «Manual»): a pré-visualização sai como espera e percebe-se o que faz cada definição? Crie a imagem final e abra-a com «Abrir com…».
28. **Novidade da 0.32**: abra **Definições → Configure o seu ASTRO**, arraste para a tela as peças que usa (ou comece com um atalho como «Noite de captação») e carregue em **«Criar o meu ASTRO»**: fica só o que escolheu? Falta-lhe alguma peça, ou alguma devia dividir-se em duas? Experimente guardá-lo para as próximas vezes ou usá-lo só numa sessão, e volte com **«Voltar ao ASTRO completo»**.
29. **Novidade da 0.33**: em **Mais opções → Juntar masters de vários equipamentos…**, escolha uma pasta com masters do mesmo objeto e filtro feitos com telescópios diferentes (seus ou de colegas): alinha-os todos? Notam-se emendas ou degraus de brilho onde acaba cada campo? Convence-o o peso dado a cada um? Ao empilhar um projeto com vários equipamentos, experimente também **«Com vários equipamentos, manter o campo maior»**.
30. Em geral: o que acha confuso ou lento, ou de que sente falta?

## Como comunicar o que encontrar
No ASTRO: **menu «Mais» → «Comunicar um problema ou sugestão»**. Escreva o que aconteceu por palavras suas; o programa acrescenta automaticamente os dados técnicos (versão, sistema e registo). **Não envia as suas fotos nem dados pessoais.** Se puder, anexe uma captura de ecrã.

Tudo serve: falhas, frases pouco claras, ideias e também aquilo de que gosta.

## Os seus dados
- Tudo fica na pasta que escolheu ao começar; o ASTRO **não envia nada para a Internet**. Apenas verifica se há versões novas; em «Próximas noites», pede a previsão do tempo ao Open-Meteo.com com a sua posição aproximada (pode ser desativado); para o plano desta noite descarrega uma vez por dia as órbitas dos satélites brilhantes do CelesTrak.org (sem enviar nada), e em «Ciência» consulta o catálogo Gaia com as coordenadas do campo que mede e, para as variáveis, a AAVSO com o nome da estrela (nunca as suas fotos); para os trânsitos, descarrega a lista de planetas do ExoClock e da NASA; para as RR Lyrae, a lista de RR Lyrae do VSX e os dados da estrela, e para os asteroides consulta o JPL com o centro do campo, a hora e a posição do seu local. Se ativar o WhatsApp automático, a mensagem passa pelo CallMeBot, um serviço gratuito de terceiros.
- O ASTRO copia as suas exposições para a sua pasta sem tocar nos originais (ou, com «Só analisar», deixa-as onde estão e apenas as lê). Ainda assim, por ser uma beta, **não apague os seus originais** enquanto testa.

## Duração
A beta vai durar cerca de **3 meses**. Todas as melhorias chegam automaticamente ao abrir o ASTRO.

*Raúl Hussein Galindo e Tomás Moreno González*
