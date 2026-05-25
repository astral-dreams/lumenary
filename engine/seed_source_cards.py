from __future__ import annotations

from .config import EngineConfig
from .source_ingestion import register_source


SOURCE_SEED = [
    {
        "title": "Brihadaranyaka Upanishad 3.7.23",
        "tradition": "advaita-vedanta",
        "source_type": "text",
        "url": "https://sacred-texts.com/hin/sbe15/sbe15070.htm",
        "notes": "Primary Upanishadic source for the unseen seer/hearer/knower and inner ruler language. High priority for Lumenary's residue-policy and remainder-pressure thread.",
    },
    {
        "title": "Chandogya Upanishad 6.8.7 Tat Tvam Asi",
        "tradition": "advaita-vedanta",
        "source_type": "text",
        "url": "https://shlokam.org/texts/Chandogya-6-8-7",
        "notes": "Primary source for the identity formula 'tat tvam asi'. Useful for testing whether identity claims function as metaphysical assertion, instruction, or recognition formula.",
    },
    {
        "title": "Mandukya Upanishad",
        "tradition": "advaita-vedanta",
        "source_type": "text",
        "url": "https://texts.wara.in/upanishads/mukhya/mandukya/",
        "notes": "Primary source for waking, dreaming, deep sleep, and turiya. Useful for comparing state models of consciousness with witness and self-negation claims.",
    },
    {
        "title": "Shankara Upadesa Sahasri",
        "tradition": "advaita-vedanta",
        "source_type": "text",
        "url": "https://www.advaita.org.uk/discourses/tattvaloka/upadesha1.htm",
        "notes": "Advaita teaching text attributed to Shankara. Useful for comparing later Advaita instruction with earlier Upanishadic language and for checking whether de-objectification becomes explicit witness ontology.",
    },
    {
        "title": "SN 22.59 Anattalakkhana Sutta",
        "tradition": "early-buddhism",
        "source_type": "text",
        "url": "https://suttacentral.net/sn22.59/en/bodhi",
        "notes": "Primary early Buddhist source for the not-self analysis of the five aggregates. Central counterpoint to Upanishadic residue and witness language.",
    },
    {
        "title": "SN 22.95 Phenapindupama Sutta",
        "tradition": "early-buddhism",
        "source_type": "text",
        "url": "https://suttacentral.net/sn22.95/en/sujato",
        "notes": "Primary source using foam, bubble, mirage, and illusion similes for the aggregates. Useful for testing whether consciousness is treated as insubstantial rather than as final witness.",
    },
    {
        "title": "MN 1 Mulapariyaya Sutta",
        "tradition": "early-buddhism",
        "source_type": "text",
        "url": "https://suttacentral.net/mn1/en/bodhi",
        "notes": "Primary source on the root of conceptual proliferation and the way different persons conceive experience. Useful for Lumenary's inference-policy and reification analysis.",
    },
    {
        "title": "Dao De Jing",
        "tradition": "daoism",
        "source_type": "text",
        "url": "https://ctext.org/dao-de-jing",
        "notes": "Primary Daoist source for dao, naming, non-forcing, and reduction. Useful for comparing apophatic naming limits with Upanishadic and Buddhist negation.",
    },
    {
        "title": "Dao De Jing Chapter 48",
        "tradition": "daoism",
        "source_type": "text",
        "url": "https://ctext.org/dictionary.pl?id=11634&if=en",
        "notes": "Focused Dao De Jing source for learning, diminishing, and wu wei. Useful for comparing negation-by-reduction with self-negation and de-identification practices.",
    },
    {
        "title": "Zhuangzi",
        "tradition": "daoism",
        "source_type": "text",
        "url": "https://ctext.org/zhuangzi",
        "notes": "Primary Daoist source for wandering, perspective shifting, fasting the heart-mind, and self-forgetting. Useful for a non-ontological model of spiritual transformation.",
    },
    {
        "title": "Plotinus Enneads",
        "tradition": "neoplatonism",
        "source_type": "text",
        "url": "https://classics.mit.edu/Plotinus/enneads.html",
        "notes": "Primary Neoplatonic source for the One, Intellect, Soul, ascent, and self-transcendence. Useful for comparing unity claims with Advaita and Sufi metaphysics.",
    },
    {
        "title": "Plotinus Enneads Fifth Ennead",
        "tradition": "neoplatonism",
        "source_type": "text",
        "url": "https://classics.mit.edu/Plotinus/enneads.5.fifth.html",
        "notes": "Focused Plotinus source for Intellect and the One. Useful for testing whether unity is framed as ontological ground, contemplative ascent, or noetic identity.",
    },
    {
        "title": "Stanford Encyclopedia of Philosophy Plotinus",
        "tradition": "neoplatonism",
        "source_type": "website",
        "url": "https://plato.stanford.edu/entries/plotinus/",
        "notes": "Scholarly overview of Plotinus and the three principles: the One, Intellect, and Soul. Use as secondary guardrail when interpreting Plotinus primary texts.",
    },
    {
        "title": "Al-Ghazali The Alchemy of Happiness",
        "tradition": "sufism",
        "source_type": "text",
        "url": "https://sacred-texts.com/isl/tah/index.htm",
        "notes": "Sufi ethical and contemplative source centered on knowledge of self, God, world, afterlife, recollection, and love. Useful for comparing self-knowledge and God-knowledge without collapsing them into nondual identity.",
    },
    {
        "title": "Attar Bird Parliament",
        "tradition": "sufism",
        "source_type": "text",
        "url": "https://sacred-texts.com/isl/bp/index.htm",
        "notes": "Abridged public-domain source related to Conference of the Birds. Useful for studying annihilation, journey structure, and allegorical self-overcoming.",
    },
    {
        "title": "Ibn al-Arabi Tarjuman al-Ashwaq",
        "tradition": "sufism",
        "source_type": "text",
        "url": "https://www.sacred-texts.com/isl/taa/index.htm",
        "notes": "Mystical odes with authorial commentary. Useful for distinguishing symbolic love language, metaphysical interpretation, and risks of over-literalizing Sufi unity claims.",
    },
    {
        "title": "Tononi Information Integration Theory of Consciousness",
        "tradition": "consciousness-science",
        "source_type": "paper",
        "url": "https://bmcneurosci.biomedcentral.com/articles/10.1186/1471-2202-5-42",
        "notes": "Foundational IIT paper proposing consciousness as integrated information. Use only as empirical-adjacent/scientific comparison; do not equate it with spiritual claims about awareness.",
    },
    {
        "title": "Global Neuronal Workspace as a Broadcasting Network",
        "tradition": "consciousness-science",
        "source_type": "paper",
        "url": "https://direct.mit.edu/netn/article/6/4/1186/111960/The-global-neuronal-workspace-as-a-broadcasting",
        "notes": "Scientific source on global neuronal workspace and broadcasting. Useful for distinguishing access-consciousness from metaphysical witness-consciousness.",
    },
    {
        "title": "An Interoceptive Predictive Coding Model of Conscious Presence",
        "tradition": "consciousness-science",
        "source_type": "paper",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC3254200/",
        "notes": "Scientific model connecting interoceptive prediction, agency, and presence. Useful for Lumenary's remainder-pressure idea as empirical-adjacent grounding.",
    },
    {
        "title": "I and Me The Self in the Context of Consciousness",
        "tradition": "consciousness-science",
        "source_type": "paper",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC6131638/",
        "notes": "Review-oriented scientific/philosophical source on selfhood and consciousness. Useful for separating narrative self, minimal self, ownership, and witness-like phenomenology.",
    },
    {
        "title": "CERN The Standard Model",
        "tradition": "high-energy-physics",
        "source_type": "website",
        "url": "https://home.web.cern.ch/science/physics/standard-model/",
        "notes": "Official CERN overview of the Standard Model. Use as a baseline map for matter particles, force carriers, the Higgs sector, and the fact that gravity is not included in the Standard Model.",
    },
    {
        "title": "Particle Data Group Review of Particle Physics",
        "tradition": "high-energy-physics",
        "source_type": "website",
        "url": "https://pdg.lbl.gov/",
        "notes": "Current Particle Data Group reference for particle properties, constants, Standard Model reviews, and experimental constraints. Use as the correction layer when a speculative idea depends on real particle-physics values.",
    },
    {
        "title": "CERN What Is Special About The Higgs Boson",
        "tradition": "matter-theory",
        "source_type": "website",
        "url": "https://home.cern/science/physics/the-higgs-boson/what/",
        "notes": "Official CERN explanation of Higgs-field mass generation and particles as field excitations. Use to discipline claims about matter as field-pattern rather than substance, while avoiding metaphysical overreach.",
    },
    {
        "title": "ATLAS Higgs Boson Discovery Paper",
        "tradition": "matter-theory",
        "source_type": "paper",
        "url": "https://arxiv.org/abs/1207.7214",
        "notes": "Primary ATLAS discovery paper for a new particle compatible with the Standard Model Higgs boson. Useful as a hard empirical anchor for Higgs-field and mass-generation discussions.",
    },
    {
        "title": "CMS Higgs Boson Discovery Paper",
        "tradition": "matter-theory",
        "source_type": "paper",
        "url": "https://arxiv.org/abs/1207.7235",
        "notes": "Primary CMS discovery paper for a boson near 125 GeV. Pair with the ATLAS paper before treating Higgs-related mass claims as experimentally grounded.",
    },
    {
        "title": "Weinberg A Model of Leptons",
        "tradition": "matter-theory",
        "source_type": "paper",
        "url": "https://doi.org/10.1103/PhysRevLett.19.1264",
        "notes": "Foundational electroweak unification paper. Use as formal-theory grounding for symmetry breaking, gauge structure, and mass terms before drawing analogies to spiritual unity or differentiation.",
    },
    {
        "title": "DOE Explains The Strong Force",
        "tradition": "matter-theory",
        "source_type": "website",
        "url": "https://www.energy.gov/science/doe-explainsthe-strong-force",
        "notes": "Department of Energy overview of the strong interaction. Use as a guardrail against the common error that the Higgs field explains all ordinary matter mass; hadronic mass requires QCD and confinement.",
    },
    {
        "title": "CERN Heavy Ions and Quark Gluon Plasma",
        "tradition": "matter-theory",
        "source_type": "website",
        "url": "https://home.cern/about/physics/heavy-ions-and-quark-gluon-plasma",
        "notes": "Official CERN source on quark-gluon plasma and matter under extreme energy density. Useful for grounding claims about matter phase, confinement, deconfinement, and the early-universe material state.",
    },
    {
        "title": "Noether Invariant Variation Problems",
        "tradition": "physics-time",
        "source_type": "paper",
        "url": "https://eudml.org/doc/59024",
        "notes": "Original Noether theorem source. Use to ground the relationship between time-translation symmetry and conservation laws before making philosophical claims about time, order, and invariance.",
    },
    {
        "title": "Einstein On The Electrodynamics Of Moving Bodies",
        "tradition": "physics-time",
        "source_type": "paper",
        "url": "https://en.wikisource.org/wiki/On_the_Electrodynamics_of_Moving_Bodies",
        "notes": "Primary special-relativity source for simultaneity, clock synchronization, and the replacement of universal time with observer-relative temporal coordinates.",
    },
    {
        "title": "Minkowski Space And Time",
        "tradition": "physics-time",
        "source_type": "lecture",
        "url": "https://en.wikisource.org/wiki/Translation:Space_and_Time",
        "notes": "Primary source for the spacetime formulation of special relativity. Use as the anchor when distinguishing experienced time, coordinate time, and four-dimensional spacetime structure.",
    },
    {
        "title": "BABAR Observation Of Time Reversal Violation",
        "tradition": "physics-time",
        "source_type": "paper",
        "url": "https://arxiv.org/abs/1207.5832",
        "notes": "Primary high-energy-physics paper reporting direct time-reversal violation in the neutral B meson system. Use for physical time-asymmetry claims, not for broad claims about psychological or cosmic time.",
    },
    {
        "title": "Anderson The Problem Of Time In Quantum Gravity",
        "tradition": "quantum-gravity-time",
        "source_type": "paper",
        "url": "https://arxiv.org/abs/1009.2157",
        "notes": "Review of the problem of time in quantum gravity. Use as a map of competing strategies: time before quantization, emergent time, timeless records, and relational observables.",
    },
    {
        "title": "Rovelli Partial Observables",
        "tradition": "quantum-gravity-time",
        "source_type": "paper",
        "url": "https://arxiv.org/abs/gr-qc/0110035",
        "notes": "Formal source for partial and complete observables. Useful for Lumenary's inference-policy work because it treats observability as relational without turning relation into mystical identity.",
    },
    {
        "title": "Page And Wootters Evolution Without Evolution",
        "tradition": "quantum-gravity-time",
        "source_type": "paper",
        "url": "https://cds.cern.ch/record/143641?ln=en",
        "notes": "Source for the idea that apparent dynamics can be represented through correlations with internal clock readings inside a stationary global description. Useful for emergent-time hypotheses.",
    },
    {
        "title": "DeWitt Quantum Theory Of Gravity The Canonical Theory",
        "tradition": "quantum-gravity-time",
        "source_type": "paper",
        "url": "https://doi.org/10.1103/PhysRev.160.1113",
        "notes": "Canonical quantum-gravity source associated with the Wheeler-DeWitt equation. Use as a historical and formal anchor for timeless wavefunction discussions, with caution about unresolved interpretation.",
    },
    {
        "title": "Sakharov CP Violation And Baryon Asymmetry",
        "tradition": "matter-antimatter",
        "source_type": "paper",
        "url": "https://www.osti.gov/biblio/4449128",
        "notes": "Foundational source for the conditions required to generate cosmic matter-antimatter asymmetry. Use to ground claims about why the universe contains matter rather than equal annihilating matter and antimatter.",
    },
    {
        "title": "CERN Antimatter",
        "tradition": "matter-antimatter",
        "source_type": "website",
        "url": "https://home.cern/science/physics/antimatter/",
        "notes": "Official CERN overview of antimatter, antimatter experiments, and the unresolved matter-antimatter asymmetry problem. Use as a current experimental-context card.",
    },
    {
        "title": "Planck 2018 Cosmological Parameters",
        "tradition": "particle-cosmology",
        "source_type": "paper",
        "url": "https://arxiv.org/abs/1807.06209",
        "notes": "Planck Collaboration cosmological-parameter paper. Use as a quantitative anchor for baryon density, dark matter density, and the matter content of the observable universe.",
    },
    {
        "title": "CERN Physics Programme",
        "tradition": "high-energy-physics",
        "source_type": "website",
        "url": "https://home.cern/science/physics/",
        "notes": "Official CERN overview of particle physics as the study of fundamental constituents of matter, plus adjacent CERN research areas. Use as a broad orientation source for the HEP corpus.",
    },
]


def main() -> None:
    config = EngineConfig.load()
    for source in SOURCE_SEED:
        _, card_path = register_source(config=config, path=None, **source)
        print(card_path.relative_to(config.root))


if __name__ == "__main__":
    main()
