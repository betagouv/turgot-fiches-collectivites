// Imported by name rather than by a URL built at run time, so that the bundler
// sees each component and includes it.

import { render as annuel } from "./financements/annuel/annuel.js"
import { render as carte } from "./financements/carte/carte.js"
import { render as financeurs } from "./financements/financeurs/financeurs.js"
import { render as historique } from "./financements/historique/historique.js"
import { render as parHabitant } from "./financements/par_habitant/par_habitant.js"
import { render as synthese } from "./financements/synthese/synthese.js"
import { render as identite } from "./identite/identite.js"
import { render as programmes } from "./programmes/programmes.js"

export const COMPONENTS = {
  identite,
  programmes,
  "financements.annuel": annuel,
  "financements.carte": carte,
  "financements.financeurs": financeurs,
  "financements.historique": historique,
  "financements.par_habitant": parHabitant,
  "financements.synthese": synthese,
}
