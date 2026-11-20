/*
 * notation-prix — les formules de notation du critère prix des marchés publics
 * français. Même calcul que le paquet Python (src/notation_prix/formules.py),
 * vérifié sur les mêmes cas (tests/cas.json).
 * Licence Apache 2.0 — Copyright 2026 Temi.
 */
(function (racine, fabrique) {
  const api = fabrique();
  if (typeof module === "object" && module.exports) module.exports = api;
  else racine.NotationPrix = api;
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  const FORMULES = {
    proportionnelle: { nom: "Méthode classique", expression: "N = max × Pmin / P", exempleDaj: "M1" },
    minmax: { nom: "Méthode linéaire", expression: "N = max × (Pmax − P) / (Pmax − Pmin)", exempleDaj: "M2" },
    moyenne: { nom: "Moyenne des offres", expression: "N = max × Pmoy / (Pmoy + P)", exempleDaj: "M3a" },
    moyenne_carree: { nom: "Moyenne au carré", expression: "N = max × Pmoy² / (Pmoy² + P²)", exempleDaj: "M3b" },
    soustractive: { nom: "Écart au moins-disant", expression: "N = max × (1 − k × (P − Pmin) / Pmin)", exempleDaj: null },
    puissance: { nom: "Classique à la puissance α", expression: "N = max × (Pmin / P)^α", exempleDaj: null },
    moyenne_beta: { nom: "Moyenne à la puissance β", expression: "N = max × Pmoy^β / (Pmoy^β + P^β)", exempleDaj: null },
    mediane: { nom: "Médiane des offres", expression: "N = max × Pmed / (Pmed + P)", exempleDaj: null },
    mediane_beta: { nom: "Médiane à la puissance β", expression: "N = max × Pmed^β / (Pmed^β + P^β)", exempleDaj: null },
  };

  const ALIAS = { classique: "proportionnelle", lineaire: "minmax", "linéaire": "minmax" };

  function cle(formule) {
    const c = ALIAS[formule] || formule;
    if (!Object.prototype.hasOwnProperty.call(FORMULES, c)) {
      throw new Error("formule inconnue : " + formule);
    }
    return c;
  }

  function mediane(valeurs) {
    const tri = valeurs.slice().sort(function (a, b) { return a - b; });
    const m = Math.floor(tri.length / 2);
    return tri.length % 2 ? tri[m] : (tri[m - 1] + tri[m]) / 2;
  }

  function part(c, p, r, k, alpha, beta) {
    switch (c) {
      case "proportionnelle": return r.min / p;
      case "minmax": return r.max - r.min > 0 ? (r.max - p) / (r.max - r.min) : 1;
      case "moyenne": return r.moy / (r.moy + p);
      case "moyenne_carree": return (r.moy * r.moy) / (r.moy * r.moy + p * p);
      case "soustractive": return 1 - (k * (p - r.min)) / r.min;
      case "puissance": return Math.pow(r.min / p, alpha);
      case "moyenne_beta": return Math.pow(r.moy, beta) / (Math.pow(r.moy, beta) + Math.pow(p, beta));
      case "mediane": return r.med / (r.med + p);
      case "mediane_beta": return Math.pow(r.med, beta) / (Math.pow(r.med, beta) + Math.pow(p, beta));
    }
    throw new Error(c);
  }

  /**
   * Les notes de prix de chaque offre, dans l'ordre des offres.
   * options : { bareme = 10, ecartees = [], k = 1, alpha = 1, beta = 2 }.
   * Une offre écartée reçoit null et ne compte ni dans Pmin, ni dans Pmax,
   * ni dans la moyenne, ni dans la médiane.
   */
  function noter(prix, formule, options) {
    const o = options || {};
    const c = cle(formule || "proportionnelle");
    const bareme = o.bareme === undefined ? 10 : o.bareme;
    const k = o.k === undefined ? 1 : o.k;
    const alpha = o.alpha === undefined ? 1 : o.alpha;
    const beta = o.beta === undefined ? 2 : o.beta;
    if (!(typeof bareme === "number" && isFinite(bareme) && bareme > 0)) {
      throw new Error("le barème doit être un nombre strictement positif");
    }
    const n = prix.length;
    if (n === 0) throw new Error("aucune offre à noter");
    const exclues = new Set(o.ecartees || []);
    exclues.forEach(function (i) {
      if (!(Number.isInteger(i) && i >= 0 && i < n)) throw new Error("offre écartée inconnue : " + i);
    });

    const retenus = new Map();
    for (let i = 0; i < n; i++) {
      if (exclues.has(i)) continue;
      const v = Number(prix[i]);
      if (typeof prix[i] === "boolean" || prix[i] === null || prix[i] === "" || !isFinite(v) || v <= 0) {
        throw new Error("offre " + i + " : le prix doit être strictement positif");
      }
      retenus.set(i, v);
    }
    if (retenus.size === 0) throw new Error("toutes les offres sont écartées : aucune note possible");

    const valeurs = Array.from(retenus.values());
    const r = {
      min: Math.min.apply(null, valeurs),
      max: Math.max.apply(null, valeurs),
      moy: valeurs.reduce(function (s, v) { return s + v; }, 0) / valeurs.length,
      med: mediane(valeurs),
    };

    const notes = [];
    for (let i = 0; i < n; i++) {
      if (!retenus.has(i)) { notes.push(null); continue; }
      const x = part(c, retenus.get(i), r, k, alpha, beta);
      // Pas de note négative (CE, 18 décembre 2012, n° 362532), ni au-delà du maximum.
      notes.push(bareme * Math.min(1, Math.max(0, x)));
    }
    return notes;
  }

  /** Les notes selon plusieurs formules ; par défaut, les quatre exemples de la fiche DAJ. */
  function comparer(prix, formules, options) {
    const liste = formules || Object.keys(FORMULES).filter(function (f) { return FORMULES[f].exempleDaj; });
    const sortie = {};
    liste.forEach(function (f) { sortie[f] = noter(prix, f, options); });
    return sortie;
  }

  /**
   * Arrondi au plus proche, la demie vers le haut (2,5 donne 3). L'arrondi se fait
   * sur l'écriture décimale la plus courte du nombre (1,005 et non 1,00499999…),
   * comme Decimal(repr(note)) côté Python.
   */
  function arrondir(note, decimales) {
    if (note === null || note === undefined) return null;
    const d = decimales || 0;
    let texte = String(Math.abs(note));
    if (/e/i.test(texte)) texte = Math.abs(note).toFixed(20);
    const morceaux = texte.split(".");
    const entier = morceaux[0];
    const fraction = (morceaux[1] || "").padEnd(d + 1, "0");
    const chiffres = (entier + fraction.slice(0, d)).split("").map(Number);
    if (Number(fraction.charAt(d)) >= 5) {
      let i = chiffres.length - 1;
      while (i >= 0 && chiffres[i] === 9) { chiffres[i] = 0; i--; }
      if (i < 0) chiffres.unshift(1); else chiffres[i] += 1;
    }
    const s = chiffres.join("");
    const valeur = Number(d ? s.slice(0, s.length - d) + "." + s.slice(s.length - d) : s);
    return note < 0 ? -valeur : valeur;
  }

  /** Le rang de chaque offre (1 = la mieux notée) ; deux notes égales ont le même rang. */
  function classer(notes) {
    const notees = notes.filter(function (n) { return n !== null; });
    return notes.map(function (n) {
      return n === null ? null : 1 + notees.filter(function (a) { return a > n; }).length;
    });
  }

  return { FORMULES: FORMULES, ALIAS: ALIAS, noter: noter, comparer: comparer, arrondir: arrondir, classer: classer };
});
