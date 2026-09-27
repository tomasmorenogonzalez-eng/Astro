# Firmar ASTRO (Mac y Windows)

La fábrica de GitHub (`.github/workflows/fabricar.yml`) ya está preparada para **firmar y notarizar en Mac** y **firmar en Windows**. Solo hace falta conseguir los certificados y guardarlos como *secrets* del repositorio. Mientras no estén, ASTRO se sigue fabricando igual que ahora, sin firmar.

**Qué cambia al firmar**
- **Mac:** sin firma, el Mac dice que no puede comprobar el desarrollador y hay que ir a *Ajustes del Sistema → Privacidad y seguridad → Abrir igualmente*. Firmado y notarizado por Apple, ASTRO se abre con doble clic como cualquier aplicación.
- **Windows:** sin firma, SmartScreen muestra «Windows protegió su PC» y hay que pulsar *Más información → Ejecutar de todas formas*. Firmado, aparece tu nombre como editor. Aun así, SmartScreen puede avisar las primeras semanas, hasta que el certificado gana «reputación».

Los *secrets* se guardan en GitHub, en el repositorio: **Settings → Secrets and variables → Actions → New repository secret**. Nadie puede leerlos después, ni siquiera tú: solo los usa la fábrica.

---

## Mac (lo recomendable)

**Qué necesitas**
1. **Apple Developer Program**, a tu nombre y con tu Apple ID: 99 USD al año. Te das de alta en <https://developer.apple.com/programs/>. Tu Apple ID necesita la verificación en dos pasos. Apple puede tardar uno o dos días en aprobarte.
2. **Un certificado «Developer ID Application».** Solo puede crearlo el titular de la cuenta. Hay dos maneras:
   - **Con Xcode:** *Ajustes → Cuentas → Gestionar certificados → + → Developer ID Application*.
   - **En la web:** <https://developer.apple.com/account/resources/certificates>, con una solicitud que se crea en *Acceso a Llaveros → Asistente para certificados → Solicitar un certificado de una autoridad de certificación*.
3. **Exporta el certificado como .p12.** En *Acceso a Llaveros → Mis certificados*, clic derecho en «Developer ID Application: …» → *Exportar*. Ponle una contraseña.
4. **Pásalo a texto** en el Terminal con `base64 -i certificado.p12 | pbcopy`. El texto queda copiado.
5. **Crea una contraseña para apps.** En <https://appleid.apple.com>, entra en *Inicio de sesión y seguridad → Contraseñas específicas de apps* y crea una llamada «ASTRO notarización».
6. **Busca tu Team ID.** Son 10 letras y números, en <https://developer.apple.com/account>, en *Membership details*.

**Secrets que hay que crear**

| Nombre | Qué va |
|---|---|
| `MAC_CERT_P12` | el texto del paso 4 |
| `MAC_CERT_PASSWORD` | la contraseña con la que exportaste el .p12 |
| `APPLE_ID` | el correo de tu Apple ID |
| `APPLE_APP_PASSWORD` | la contraseña para apps del paso 5 |
| `APPLE_TEAM_ID` | el Team ID del paso 6 |

Después, publica una versión nueva. La fábrica firma ASTRO para Apple Silicon y para Intel y lo manda a Apple para la notarización, que tarda unos minutos. Cuando Apple lo aprueba, le «grapa» el visto bueno y comprueba que el Mac lo aceptará. Si falta algo, la fábrica se para y dice qué secret falta.

---

## Windows (opcional)

Desde junio de 2023, los certificados para firmar programas tienen que guardarse en un dispositivo seguro: un token USB o una «caja fuerte» en la nube. Con un token USB no se puede firmar en GitHub, así que hace falta una de estas opciones:

- **a) Azure Artifact Signing (antes «Trusted Signing»), de Microsoft.**
  - Cuesta unos 10 USD al mes y está hecho para firmar en GitHub.
  - Como persona física solo se puede usar en Estados Unidos y Canadá.
  - Como organización sí se puede usar desde la Unión Europea. Por ejemplo, podría darse de alta la asociación, con su CIF, y entonces aparecería como editora de ASTRO. Microsoft comprueba la identidad de la organización y su historial, así que conviene mirar antes si la asociación cumple los requisitos.
  - Hay que crear estos **secrets**: `AZURE_TENANT_ID`, `AZURE_CLIENT_ID` y `AZURE_CLIENT_SECRET`, de una «aplicación» de Azure con el rol *Artifact Signing Certificate Profile Signer*.
  - Y estas **variables**, en la pestaña *Variables* de la misma página:
    - `AZURE_SIGNING_ENDPOINT` (por ejemplo `https://weu.codesigning.azure.net`);
    - `AZURE_SIGNING_ACCOUNT`, el nombre de la cuenta de firma;
    - `AZURE_SIGNING_PROFILE`, el perfil del certificado.
  - La fábrica usa la herramienta `sign` de Microsoft. La primera vez conviene mirar lo que dice ese paso, por si Microsoft ha cambiado el nombre de alguna opción.
- **b) Certificado de una autoridad de certificación: Sectigo, Certum, SSL.com, DigiCert…**
  - Cuesta entre 100 y 400 € al año.
  - Hay que elegir la opción de **firma en la nube** de esa autoridad, no el token USB. Dímelo cuando lo tengas y adapto el paso a su herramienta.
  - Si te dieran un archivo **.pfx** exportable, lo cual hoy es raro, basta con dos secrets: `WIN_CERT_PFX` (el .pfx en texto, con `certutil -encode` o `base64`) y `WIN_CERT_PASSWORD`.
- **c) Dejar Windows sin firmar,** como ahora. Funciona igual; solo sale el aviso de SmartScreen la primera vez.

**Recomendación:** firmar en Mac, porque 99 USD al año quitan el aviso más molesto. En Windows, esperar, o hacerlo a través de la asociación con Azure si os interesa.

---

## La versión 1.0

Las versiones 0.x llevan la etiqueta «BETA». Cuando quieras la primera versión definitiva, publica una versión con la etiqueta **`v1.0`**. Mejor hacerlo después de guardar los secrets, para que ya salga firmada. Los ordenadores que tengan la beta se actualizarán solos a la 1.0.

---

## In English

The GitHub build is ready to sign and notarize on macOS and to sign on Windows. It only needs repository secrets:
- **macOS:** `MAC_CERT_P12` (Developer ID Application certificate as base64 .p12), `MAC_CERT_PASSWORD`, `APPLE_ID`, `APPLE_APP_PASSWORD` (app-specific password) and `APPLE_TEAM_ID`. Apple Developer Program: 99 USD/year.
- **Windows:** either `WIN_CERT_PFX` + `WIN_CERT_PASSWORD`, or Azure Artifact Signing. For Azure, set the secrets `AZURE_TENANT_ID`, `AZURE_CLIENT_ID` and `AZURE_CLIENT_SECRET`, and the variables `AZURE_SIGNING_ENDPOINT`, `AZURE_SIGNING_ACCOUNT` and `AZURE_SIGNING_PROFILE`. Azure only accepts individuals in the US and Canada; organisations in the EU can use it.

Without these secrets the build carries on unsigned, exactly as before.
