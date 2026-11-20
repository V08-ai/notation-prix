import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { noter, comparer, arrondir, classer, FORMULES } = require("../docs/notation.js");
const CAS = JSON.parse(readFileSync(new URL("./cas.json", import.meta.url), "utf8"));

const daj = CAS.fiche_daj_2024;
for (const [formule, attendu] of Object.entries(daj.attendu_arrondi)) {
  test(`fiche DAJ 2024 : ${formule}`, () => {
    const notes = noter(daj.prix, formule, { bareme: daj.bareme });
    assert.deepEqual(notes.map((n) => arrondir(n)), attendu);
  });
}

for (const cas of CAS.calculs) {
  test(cas.nom, () => {
    const notes = noter(cas.prix, cas.formule, {
      bareme: cas.bareme, ecartees: cas.ecartees, k: cas.k, alpha: cas.alpha, beta: cas.beta,
    });
    cas.attendu.forEach((attendu, i) => {
      if (attendu === null) assert.equal(notes[i], null);
      else assert.ok(Math.abs(notes[i] - attendu) <= 1e-9 * Math.max(1, Math.abs(attendu)), `${notes[i]} ≠ ${attendu}`);
    });
  });
}

test("la formule change les écarts, pas l'ordre", () => {
  const notes = comparer(daj.prix, null, { bareme: 10 });
  for (const f of Object.keys(notes)) assert.deepEqual(classer(notes[f]), [1, 2, 3, 4, 5]);
  assert.deepEqual(["proportionnelle", "minmax", "moyenne"].map((f) => arrondir(notes[f][4])), [2, 0, 3]);
  assert.ok(notes.moyenne[0] < 10);
});

test("avec la valeur technique, la formule change le gagnant", () => {
  const technique = [55, 70, 80, 90, 95];
  const gagnants = {};
  for (const [f, notes] of Object.entries(comparer(daj.prix, null, { bareme: 10 }))) {
    const totaux = notes.map((n, i) => 0.4 * n * 10 + 0.6 * technique[i]);
    gagnants[f] = "ABCDE"[classer(totaux).indexOf(1)];
  }
  assert.deepEqual(gagnants, { proportionnelle: "A", minmax: "C", moyenne: "D", moyenne_carree: "C" });
});

test("toutes les formules restent dans le barème", () => {
  for (const f of Object.keys(FORMULES)) {
    for (const n of noter([1, 37, 120, 950, 1e7], f, { bareme: 20, k: 3, alpha: 4, beta: 5 })) {
      assert.ok(n >= 0 && n <= 20);
    }
  }
});

test("erreurs", () => {
  assert.throws(() => noter([], "minmax"), /aucune offre/);
  assert.throws(() => noter([100, 0], "minmax"), /strictement positif/);
  assert.throws(() => noter([100, 200], "minmax", { ecartees: [0, 1] }), /toutes les offres/);
  assert.throws(() => noter([100], "au_hasard"), /formule inconnue/);
});

test("arrondir : la demie vers le haut", () => {
  assert.equal(arrondir(2.5), 3);
  assert.equal(arrondir(6.666, 1), 6.7);
  assert.equal(arrondir(1.005, 2), 1.01);
  assert.equal(arrondir(9.995, 2), 10);
  assert.equal(arrondir(null), null);
});

test("classer", () => {
  assert.deepEqual(classer([10, 7, null, 10, 3]), [1, 3, null, 1, 4]);
});
