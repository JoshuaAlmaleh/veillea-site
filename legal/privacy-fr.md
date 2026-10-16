# Politique de confidentialité

> **ÉBAUCHE. Non en vigueur. Ce document doit être révisé par un avocat avant sa publication.** Les éléments marqués [QUESTION POUR JOSHUA] doivent d'abord être réglés.

**Date d'entrée en vigueur :** [DATE D'ENTRÉE EN VIGUEUR]

Veillea (« Veillea », « nous ») est une entreprise individuelle exploitée par Joshua Almaleh, NEQ 2282674748, C.P. 311, Hudson (Québec) J0P 0A9. La présente politique explique quels renseignements personnels nous recueillons par le site veillea.ca et l'application Veillea à app.veillea.ca (le « Service »), pourquoi, et quels sont vos droits. Elle vise à respecter la *Loi sur la protection des renseignements personnels dans le secteur privé* du Québec, telle que modifiée par la Loi 25, ainsi que la *Loi sur la protection des renseignements personnels et les documents électroniques* (LPRPDE) fédérale.

## 1. Responsable de la protection des renseignements personnels

Joshua Almaleh, propriétaire, est la personne responsable de la protection des renseignements personnels chez Veillea.
Pour le joindre : bonjour@veillea.ca · C.P. 311, Hudson (Québec) J0P 0A9.

## 2. Renseignements recueillis

**Compte.** À la création d'un compte, nous recueillons :
- votre adresse courriel;
- un mot de passe, conservé uniquement sous forme de hachage scrypt salé, jamais lisible;
- votre nom (facultatif);
- le nom de votre organisation;
- votre langue;
- le forfait choisi.

Nous enregistrons aussi la date de création du compte, la confirmation ou non de votre adresse courriel et la date de votre dernière connexion.

**Membres de l'équipe.** Si le propriétaire du compte ajoute un membre, nous conservons son adresse courriel, son nom (facultatif) et son rôle (propriétaire ou membre).

**Profils de veille.** Nous conservons les éléments que vous choisissez :
- vos mots-clés et mots exclus;
- vos codes de catégorie (UNSPSC/GSIN);
- vos régions et vos sources;
- les alertes auxquelles vous vous êtes désabonné.

Ces renseignements décrivent ce que votre entreprise recherche et sont liés à votre compte.

**Facturation.** Les paiements sont traités par Stripe. Nous ne recevons ni ne conservons votre numéro de carte. Stripe recueille vos données de paiement et votre adresse de facturation. Nous conservons seulement :
- vos identifiants de client et d'abonnement Stripe;
- votre forfait et la périodicité de facturation;
- l'état de l'abonnement et la date de fin de période;
- la date d'annulation prévue, s'il y a lieu.

**Utilisation et données techniques.** Notre serveur tient un journal technique des requêtes : date, méthode, page demandée, code de réponse. Les requêtes passent par Cloudflare, qui traite votre adresse IP pour acheminer le trafic et protéger le Service. [QUESTION POUR JOSHUA : confirmer si des journaux du serveur ou de Cloudflare conservent l'adresse IP des visiteurs, et pendant combien de temps.]

Nous enregistrons aussi les alertes envoyées pour chaque profil et les événements du compte (par exemple un début d'essai, une annulation ou une prolongation d'essai).

**Clés d'API.** Si votre forfait comprend l'accès à l'API, nous ne conservons qu'un hachage de votre clé.

**Communications.** Si vous nous écrivez, nous conservons votre message et notre réponse.

Nous ne recueillons aucun renseignement sensible. Le Service ne s'adresse pas aux personnes de moins de 14 ans.

## 3. Pourquoi nous les utilisons

Nous utilisons ces renseignements pour :
- créer et sécuriser votre compte, et vous connecter (témoin de session, réinitialisation du mot de passe, confirmation du courriel);
- fournir le Service : comparer les avis d'appels d'offres publics à vos profils et vous envoyer des alertes par courriel, à la fréquence de votre forfait;
- gérer votre forfait, l'essai gratuit, la facturation et l'annulation;
- envoyer des messages liés au Service : confirmation du courriel, réinitialisation du mot de passe, alertes, avis de facturation et de compte, et un message à la fin d'un abonnement;
- surveiller le Service, prévenir les abus et corriger les problèmes. Le propriétaire reçoit des avis internes sur les inscriptions et les changements d'abonnement;
- respecter nos obligations légales, par exemple la tenue des registres comptables.

Nous ne vendons ni ne louons aucun renseignement personnel, et nous ne les utilisons pas à des fins publicitaires. [QUESTION POUR JOSHUA : confirmer qu'aucun courriel de marketing ou infolettre n'est envoyé aux utilisateurs. Sinon, il faut un consentement distinct au sens de la Loi canadienne anti-pourriel (LCAP).]

## 4. Témoins et technologies semblables

**Dans l'application (app.veillea.ca) :**
- un témoin de session, nécessaire pour rester connecté. Il est HttpOnly et dure au plus 30 jours ou jusqu'à la déconnexion;
- un témoin de langue, conservé jusqu'à 1 an.

**Sur le site (veillea.ca) :** votre choix de langue est enregistré dans le stockage local de votre navigateur.

Aucun témoin d'analyse, de publicité ou de pistage n'est utilisé.

Les deux sites chargent des polices de Google Fonts. Votre navigateur transmet donc votre adresse IP à Google au chargement d'une page. Le compteur en direct de veillea.ca interroge aussi app.veillea.ca pour obtenir des chiffres publics. [QUESTION POUR JOSHUA : garder Google Fonts ou héberger les polices nous-mêmes?]

## 5. Confidentialité par défaut

Le Service ne recueille que ce qui est nécessaire à son fonctionnement, et aucun pistage facultatif n'est activé. Vous pouvez désactiver les alertes à partir de n'importe quel courriel d'alerte (lien de désabonnement) ou de votre compte.

## 6. Fournisseurs et communication à l'extérieur du Québec

Nous faisons appel aux fournisseurs suivants. Ils traitent des renseignements pour notre compte, uniquement aux fins indiquées :

| Fournisseur | Fin | Lieu |
|---|---|---|
| Stripe | Traitement des paiements, factures, portail client | États-Unis et autres pays |
| Resend | Envoi des courriels (alertes, messages du compte) | États-Unis |
| Cloudflare | DNS, connexion sécurisée à l'application, protection du réseau | Réseau mondial |
| GitHub (Microsoft) | Hébergement du site veillea.ca (GitHub Pages) | États-Unis |
| Google Fonts | Polices du site (adresse IP seulement) | États-Unis |
| [QUESTION POUR JOSHUA : où roulent physiquement le serveur de l'application et sa base de données (ordinateur ou fournisseur, ville ou pays)?] | Hébergement de l'application et base de données | [?] |

Certains renseignements sont donc conservés ou traités à l'extérieur du Québec et du Canada, surtout aux États-Unis. Ils peuvent y être accessibles aux autorités selon les lois locales.

Avant une telle communication, nous évaluons la protection dont les renseignements bénéficieront, comme l'exige l'article 17 de la Loi. Nos fournisseurs sont liés par des ententes qui la protègent. [QUESTION POUR JOSHUA : confirmer que les conditions de traitement des données de Stripe, Resend et Cloudflare sont acceptées, et si une évaluation écrite des transferts a été faite.]

## 7. Conservation

Nous conservons vos renseignements personnels tant que votre compte est actif. Ils sont supprimés :
- à la fermeture de votre compte (sur demande à bonjour@veillea.ca), ou
- à la fin de votre accès payant après une annulation. Vous gardez l'accès jusqu'à la fin de la période déjà payée; votre compte, vos profils et vos autres renseignements personnels sont ensuite supprimés. [QUESTION POUR JOSHUA : délai de suppression après cette date (p. ex. dans les 30 jours, sauvegardes comprises)?]

Exceptions : les dossiers de paiement et de facturation sont conservés par Stripe, et les factures et registres comptables que Veillea doit garder sont conservés aussi longtemps que l'exigent les lois fiscales et comptables (en général 6 ans). [QUESTION POUR JOSHUA : durée de conservation des journaux techniques et des comptes Gratuits inactifs?]

## 8. Vos droits

Vous pouvez :
- demander l'accès aux renseignements personnels que nous détenons sur vous;
- les faire rectifier s'ils sont inexacts, incomplets ou périmés;
- retirer votre consentement, par exemple en vous désabonnant des alertes ou en fermant votre compte;
- demander leur suppression ou la cessation de leur diffusion, dans les cas prévus par la loi;
- obtenir les renseignements que vous nous avez fournis dans un format technologique structuré et couramment utilisé (portabilité).

Pour exercer un droit, écrivez à bonjour@veillea.ca. Nous pourrions devoir vérifier votre identité, et nous répondrons dans un délai de 30 jours. Vous pouvez aussi porter plainte à la Commission d'accès à l'information du Québec (cai.gouv.qc.ca) ou au Commissariat à la protection de la vie privée du Canada (priv.gc.ca).

## 9. Sécurité

- Les mots de passe sont hachés (scrypt).
- Les connexions passent par HTTPS.
- Les témoins de session sont HttpOnly.
- Seul le propriétaire a un accès administrateur.

Aucune méthode n'est parfaitement sûre.

## 10. Incidents de confidentialité

En cas d'incident de confidentialité touchant des renseignements que nous détenons :
- nous prenons des mesures raisonnables pour diminuer le risque de préjudice;
- nous consignons l'incident dans un registre;
- s'il présente un risque de préjudice sérieux, nous avisons la Commission d'accès à l'information, le Commissariat à la protection de la vie privée du Canada et les personnes concernées, comme l'exige la loi.

## 11. Modifications

Nous pouvons modifier la présente politique. La date d'entrée en vigueur sera alors mise à jour. Pour un changement important, nous aviserons les titulaires de compte par courriel avant son entrée en vigueur.

## 12. Nous joindre

Joshua Almaleh, responsable de la protection des renseignements personnels : bonjour@veillea.ca · C.P. 311, Hudson (Québec) J0P 0A9.
