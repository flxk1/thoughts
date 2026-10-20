# Whether an action may take effect

*A governance language for AI agents, and the conformance suite that tests it*

**Abstract.** AI agents now cause external effects: they call tools, move data and delegate work to other agents. The rules that should govern those effects are written in prose, prompts, workflow code and access-control configuration. Standards such as XACML and ODRL give some of them a precise semantics, but both decide a request about a resource; the token here names no resource. It is an action with a kind and a risk, and the question is whether it may take effect. I present Loomground Governance, a small declarative language in which a governance policy is a graph of actors, gates and a single release point, the *master*. Evaluation assigns each gate one of five verdicts by priority selection, propagates verdicts along pipes as a join on a finite chain, and releases an action only when the effective verdict is `auto`. Execution is the host's, and the decision binds only where the host mediates every effect. Much of this is assembled from earlier work, and the paper says which parts.

What the paper contributes is how conformance to the language is tested. The semantics is published as an executable specification with 75 conformance vectors, whose runners check the reason for every rejection, compare the whole observation and test determinism under repeated and permuted runs. The suite is then tested itself: nine stubs that each break a runner rule and sixteen mutants that each break a rule of the semantics are scored through it. All nine stubs and fifteen mutants fail; the one that passes shows that no vector distinguished a `risk >=` guard from an equality. Two evaluators pass every vector and agree on eleven further probes, which is differential testing and not the independent interoperability the specification sets as its exit criterion. Each claim the language makes is set against the vectors that exercise it, and the three the suite does not reach are named.

I write the code and this text with Loomground agents, using Claude and Codex as tools, and I read and correct all of it.

<!--SECTION intro-->
## 1. Introduction

The governance question for an autonomous agent is no longer only *what may this system generally do?* It is *under which observable conditions may this particular action take effect?* An agent that drafts a document, decides a credit application and sends a payment performs three actions with different consequences, possibly on behalf of different principals, under different obligations to involve a human.

Today the constraints on such actions live in formats that are not connected: legal and policy prose, system prompts, workflow logic, access-control configuration, model-specific guardrails, approval processes and audit logs. They share a vocabulary ("policy", "human oversight", "approval", "prohibition", "escalation") but no shared, observable contract for when an agent's action may take effect, against which two runtimes could be compared. I stated the problem bluntly in the project's README: *“Every governance tool defines "policy", "gate" and "verdict" its own way; nothing is comparable or checkable.”* [LG, README].

A policy in the language is short enough to show whole. This one is the conformance vector `draft-decide-run`:

```
actor  bot7
human  alice  role legal
gate   draft   risk low    grant bot7
gate   decide  risk high   grant bot7
reserve automated_decision by legal when risk >= high
cord bot7   -> draft
cord bot7   -> decide
cord draft  -> master
cord decide -> master
```

A routine low-risk token proposed by `bot7` at `draft` is released. A high-risk automated decision proposed at `decide` is reserved for the legal role, and the master withholds it, whatever grade `bot7` holds, provided an authorising grant exists at all. The language expresses the reservation and the referral; the human process that follows is the host's (§4.5). Section 3 defines the constructs and §4 the evaluation.

This paper treats the gap as a problem of language design and interoperability. It asks one question:

> **RQ.** Can governance constraints over agent actions be stated in a small declarative language whose semantics is precise enough that separately built evaluators can be tested for observational equivalence?

The paper makes five contributions.

1. **A language.** A graph model with four node classes, three cord types and a five-verdict chain that expresses authority, human reservation, prohibition, delegation, purpose and release.
2. **A semantics** that separates verdict assignment at one gate (priority selection) from propagation across gates (a join), with a single release rule and an ordered, verdict-labelled record.
3. **An executable specification**: normative prose, grammar, schemas, vocabularies and 75 conformance vectors, with a test that every feature reaches a vector and runners that check why an input is rejected, not only that it is.
4. **A suite shown to discriminate**, by stubs that break the runners' rules and by mutants that each break one rule of the semantics. The scores are in §6; the one mutant the suite does not catch names a gap in it.
5. **An evaluation** by replication and differential probing of two evaluators, which reproduces the suite and tests claims beyond it, with an account of what 75 of 75 establishes and of what it does not.

The paper makes no claim of legal compliance. The specification itself rules that out: *“Expressing a measure in this language does not, by itself, satisfy any legal obligation”* [LG, SPEC §1].

<!--SECTION related-->
## 2. Background and related work

**The decision/enforcement split.** The separation of the function that decides from the function
that enforces is older than the policy languages built on it. ITU-T X.812, published identically as
ISO/IEC 10181-3, defines an access control decision function and an enforcement function that
admits only what the decision function allows [X812, 3.4.3–3.4.4, 5.2.1]. The names policy decision
point and policy enforcement point are the IETF's [RFC2753; RFC3198], and XACML's glossary maps
them back to ISO/IEC 10181-3 [XACML, glossary]. The master is the decision function for release, one value for each terminal gate; the
enforcement point that acts on it is the host's, and the principle it must satisfy is complete
mediation [PROT].

**Attribute-based authorisation.** RBAC [RBAC] and ABAC [ABAC] are the established models. XACML
standardises attribute-based authorisation on that split, with combining algorithms for conflicting
rules and obligations the enforcement point must discharge before a permit takes effect [XACML,
§7.2.1–7.2.2]. ODRL expresses permissions, prohibitions and duties, and defines no evaluation
semantics; the community group drafting one says the absence has hindered adoption [ODRL; ODRL-FS].
Cedar comes with a formal model and machine-checked properties [CEDAR]; Rego is Datalog-inspired
[OPA]. Three choices here are XACML's: one verdict at a gate by priority selection is
`first-applicable`, propagating by the most restrictive is `deny-overrides`, and a vector suite as
the conformance criterion is this family's practice, with OASIS shipping one of several hundred
cases [XACML-CONF]. The difference is the chain. XACML's four decisions are unordered, and the policy author selects
one of twelve combining algorithms to say how they combine; here the five verdicts form a chain and
combine by one join. That is a restriction, and its cost is every combination the chain cannot
express. XACML also has no decision that refers an action to a human: a referral is an obligation
attached to a `Permit`, and the enforcement point *“SHALL permit access only if it understands and
it can and will discharge those obligations”* [XACML, §7.2.1]. The referral is discharged outside
the decision; here it is the verdict.

**Policy languages for agents.** Two of this language's moves are twenty years old. Rei assigns
priorities over policies and sets precedence between modalities [REI]; priority selection is that
device. Ponder's `refrain` states what a subject must not do even where it holds the authorisation
[PONDER]; a restriction no grant overrides is that. KAoS instead deconflicts before runtime,
rewriting the policy set by subsumption [KAOS]. Tonti and colleagues
record of Rei that its engine "has not been designed to enforce the policies but only to reason
about them" [TONTI, §4]. `refrain` is enforced at the subject, so a non-compliant subject defeats
it. Here release is a value of the semantics, decided by the master as one function outside every subject; whether the decision
binds is then the host's, which must mediate every effect (§4.5, §7.4). Against KAoS the difference
is a disagreement: KAoS treats autonomy as a dial that policy bounds [SCERRI]; here the dial is
refused for reserved kinds, because reservation matching does not depend on grade.

**Normative systems.** This tradition already names what the reservation is. Jones and Sergot
characterise institutionalised power: an act has institutional effect only where the institution
recognises the actor as empowered to produce it [JONES; SERGOT]. Grossi, Aldewereld and Dignum
distinguish regimentation, where the design makes violation impossible, from enforcement, where the
institution reacts to one [GROSSI]. Boella and van der Torre separate substantive norms, which bind
the actor, from procedural norms, which bind the institution's own processing [BOELLA-PROC], and
analyse when delegation of power may legitimately amplify [BOELLA-DEL]. A reserved kind is
therefore a procedural norm, regimented rather than enforced, and within the model it plays the part of a Hohfeldian disability:
no delegation, grant or grade confers power to release an action of that kind. Executable
institutional specifications are likewise not new [ARTIKIS; INSTAL; AMELI; NPL; 2OPL]. The
difference is that the semantics here is single-valued, one verdict per gate and one effective
verdict per action, where an answer-set formulation yields a set of models; a vector with one
expected observation is the natural conformance interface for the former, and the latter would
have to state its expected output as a set of models. Selecting one verdict by priority is the superiority
relation of defeasible deontic logic [VONWRIGHT; IOLOGIC; GOVERNATORI].

**Composition.** The propagation rule follows the lattice model of secure information flow [IFC;
FLUME]. Myers and Liskov's decentralised label model joins labels along edges and declassifies at a
designated point [MYERS], which is this design's shape. Bruns and Huth treat a policy as a
four-valued predicate over the Belnap bilattice and compose with its operators [PBEL; LI-COMB]. The
composition algebra is therefore not the contribution: a join on a chain is the least general case
of what PBel provides. The design choice is the five-element chain, and in particular that `human` sits
below `refused`: a referral withholds, but it is not a denial. Chopra, Christie and Singh hold that a central mediation point
couples parties and should be designed away [BSPL]; a release decision is not an interaction
protocol, and the single point is what is being specified.

**Runtime governance of agents.** The Rei lineage reaches the present problem directly: AgenticRei
evaluates OWL deontic policies at runtime, outside the model, returning permit, prohibit or a
default deny [AGENTICREI]. Two proposals of 2026 occupy ground claimed here. Kaul, Lan and Gupta
compose three authorities conservatively into permitted, reviewed or denied before execution, with
receipts supporting independent replay [AGENTBOUND]. Millstone and colleagues authorise the typed
operation, gate with deny or hold, and prove that agent policy cannot widen a data owner's ceiling
and, under stated conditions, that the plan is order-independent [OBPE]. Tripathi and colleagues prove a join over ordered
governance profiles to be the least upper bound [TRIPATHI]; Tallam adjudicates once across five
planes [TALLAM]; Uchibeke binds authorisation to a passport carrying an assurance level [OAP],
which is the construct a reservation on kind makes irrelevant. Others constrain agents by
trigger-predicate rules, by temporal specifications over traces, or by scoped delegation
[AGENTSPEC; VIGIL; SOUTH]. Attenuation is stated more strongly elsewhere than as an invariant —
proved, bounded syntactically, made unrepresentable, or stated normatively [OCAP; SECPAL; IBRAHIM;
CAPMAS; AIP]. Here it is inherited, and tested by vectors rather than proved.

**What remains.** Three results bear on claims made here. Policies evaluated per action cannot see
a violation that lives in a sequence [PATHS]; the token's `provenance` is a partial answer.
User-authored permission policies blocked less overreach than per-action approval [YAN];
reservations here are authored on kind by the policy owner, not by the supervising user. Approval
can be hijacked between understanding and execution [LOOP]; the `human` verdict is assigned to
one token, whose declared fields and observed facts the log entry carries, and is re-checked at the
master against that same token (§4.4); what a later human execution is bound to is the host's (§4.5). Searches of the ACM, IEEE and arXiv indexes and of the
ISO/IEC, OASIS and W3C catalogues, run in October 2026 for policy languages, access control, agent
governance, normative systems and oversight standards, found none of four things:
an order over outcomes in which a reservation and a prohibition are values distinct from a refusal;
a referral that is a verdict in its own right, with the role it refers to read from the reservation that assigned it; a typed policy graph as the
policy object; a reservation whose match is independent of the actor and the actor's grade. Three-valued orders are now common
[AGENTBOUND; OBPE], and OBPE names an approval route on its hold, as a parameter rather than a
verdict. On the second, the nearest alternative lets the subject override a denial by accepting
obligations [RUMPOLE]. A search that does not find a thing is
not a proof of absence. These are positions, and the places where a counterexample would be most
informative.

**Standards.** ISO/IEC 22989 gives seven levels of automation, of which levels 0 to 5 are the SAE
driving-automation levels [SAE-J3016] and only level 6 is named autonomy; the standard states that
it does not use the term autonomous for automation [ISO22989, 5.13]. This language governs only
heteronomous operation in that sense, and a `grade` names latitude within external control. The
standards-side counterpart to the reservation is in preparation: ISO/IEC TS 8200 specifies
controllability including the control transfer process [TS8200], and ISO/IEC 42105 extends it for
human oversight [ISO42105]. Separation of duty is keyed on the actor [CW; ISO27001; NIST80053] and
is not prior art for a reservation keyed on kind; the older statement of keying authorisation on
the task is Thomas and Sandhu's [TBAC]. Oversight obligations and logging controls elsewhere in the
standards corpus are addressed to the organisation rather than to a policy language
[NIST-AI-100-1; ISO42001; ISO38507; IEEE7007; ISO18014-3; RFC3161; ISO27002]. The record
requirement follows tamper-evident logging and time-stamping, with the mechanism left to the host
[CT; TS; LG, SPEC §7.4], and the semantics is operational [PLOTKIN]. The exit criterion for
interoperability [LG, SPEC §9] is the IETF's and W3C's [RFC2026; RFC6410; W3C-PROCESS], which XACML
met long ago.

<!--SECTION language-->
## 3. The language

I derived the language by decomposing "AI governance" into questions that can be answered at runtime, one construct per question (Table 1). I treat a construct that answers no row as a candidate for removal.

| Governance question | Loomground Governance primitive | SPEC |
| --- | --- | --- |
| Who may act? | `actor` with an explicit authority cord (`grant`) | §3, §5.1 |
| Where must governance occur? | `gate` | §3 |
| What reaches the outside world? | the single `master`, reached only by `egress` | §3, §5.1, §7.3 |
| What is being attempted? | token `kind`, observed by the host | §4 |
| How severe is it? | token `risk`, computed by the gate, raise-only | §4 |
| May an agent act unattended? | granted vs required `grade` | §6, §7.1 |
| Must a human decide? | `reserve … by <role>` gives `reserved` | §6 |
| Is the actor unauthorised? | no grant gives `refused` | §5.1, §7.1 |
| Is the action forbidden whatever the authority? | `prohibit` gives `prohibited` | §6, §7.1 |
| For whom does the agent act? | `on-behalf-of` gives the principal chain | §6 |
| For what purpose? | `mandate`, `transfer … within` | §6 |
| Can authority grow through delegation? | no-amplification and mandate-attenuation invariants | §6 |
| Can the result be audited? | an ordered, verdict-labelled log | §7.4 |

Table: Table 1. Governance questions and the construct that answers each.

A policy is a graph. Its four node classes are `actor`, `human`, `gate` and `master`; its three cord types are *authority* (actor to gate), *pipe* (gate to gate) and *egress* (gate to master) [LG, SPEC §3, §5.1]. An action enters as a *token* carrying `id`, `kind`, `risk`, `party`, `provenance`, `reversibility`, `uncertainty` and `tags` [LG, `language-card.json`]. A guard ranges over six token properties — `kind`, `risk`, `reversibility`, `uncertainty`, `party`, `tags` — and computes nothing [LG, SPEC §6]. Of these, `risk` is not a supplier's declaration but the level the gate computes from its governed table, which a gate's floor may raise above the token's declared hint [LG, SPEC §4]; a risk guard therefore reads the effective risk at the gate, and `reversibility` and `uncertainty` read the declared values. A guard never ranges over `grade`, which is a configuration attribute rather than a token field [LG, `language-card.json`, litmus]. The conformance vector `draft-decide-run` of §1 is written in this syntax. The delegation keyword is `on-behalf-of`; the observation schema projects it as the field `on_behalf_of`.

<!--SECTION semantics-->
## 4. Semantics

An action becomes a token that enters the graph at a source gate. The graph is evaluated once per activation, and only the master can release [LG, SPEC §5.2, §7].

### 4.1 Well-formedness

An ill-formed graph, or a token lacking a required field or bearing a risk outside its domain, denotes ⊥. ⊥ is not a verdict but the absence of an evaluation, and is distinct from `auto`, the bottom of the verdict chain of §4.3. A conforming implementation *“MUST reject a token lacking a required field or bearing a risk outside its domain”*; such a token *“activates no node and produces no log entry”*, and the master withholds [LG, SPEC §4, §7.3]. The default risk domain, fixed by the token schema, is `low < medium < high < critical` [LG, schema/token.schema.json].

### 4.2 Verdict assignment at one gate

Each activated gate assigns exactly one verdict by priority selection [LG, SPEC §7.1]:

1. `prohibited` if the token matches a prohibition;
2. `refused` if the proposing actor holds no grant at the gate that authorises the token (a grant may be narrowed to kinds and risk levels);
3. `reserved` if the token matches a reservation, its risk guard compared against the gate-computed risk, floor included (§3);
4. otherwise `auto` or `human` by the grade rule: `auto` if the actor's granted grade G is at least the gate's required grade R, or the gate declares no R; `human` if G is lower, or the actor is ungraded at a graded gate. A required grade may be declared only at a source gate, and the grade compared is the proposing actor's.

Prohibition therefore comes before the authority check. Prohibitions and reservations match the token's kind and its declared guards, never the actor or the actor's grade, so no grant or grade reaches a reservation: a reserved action is withheld from every actor and left to the role it names, and what that role then does is the host's process (§4.5). Actor-independence concerns the match, not the verdict: an actor without an authorising grant is `refused` before any reservation is considered.

### 4.3 Propagation

Along pipes, a gate's effective verdict is the join of its own verdict and the effective verdicts of every gate that pipes into it and is activated in the same activation. The verdicts form a finite chain, and the join is the maximum:

```latex
\text{auto} \sqsubseteq \text{human} \sqsubseteq \text{refused} \sqsubseteq \text{reserved} \sqsubseteq \text{prohibited}
```

```latex
\mathrm{eff}(g) \;=\; \mathrm{own}(g) \,\sqcup\, \bigsqcup\,\{\, \mathrm{eff}(h) : h \xrightarrow{\text{pipe}} g,\ h \text{ activated} \,\}
```

A gate that is not activated contributes no term, and a gate with no activated predecessor keeps its own verdict, since the empty join is `auto`, the bottom of the chain [LG, SPEC §7.2]. Pipes are acyclic, and the maximum on a chain is associative, commutative and idempotent, so `eff` is well-defined and the effective verdicts do not depend on traversal order. The log is a different matter: it records evaluation order, and the pipes may admit more than one topological order. The specification fixes one. Among the gates whose activated predecessors are already logged, the gate declared earliest is evaluated next, and *“a conforming implementation's log MUST match the one this rule produces”* [LG, SPEC §7.4]. The priority order at a gate and the join order disagree on the `refused`/`reserved` pair; the specification allows this, since the two orderings *“need not agree”* [LG, SPEC §7.1]. Both verdicts withhold. The priority order decides which verdict a gate assigns; the join order decides which reason a withholding should record (the most restrictive contributing verdict [LG, SPEC §7.3]), not how strongly it withholds. `reserved` above `refused` is a diagnostic precedence, not a stronger restriction: a withholding to which a reservation contributes is recorded as reserved, which is the reason a role must act, rather than as a missing grant.

![Figure 1. The verdict order, and propagation read off it, in the conformance vector `grade-join`. Actor `bot`, granted grade L2, proposes a token at source gate `screen`, which requires L3, so `screen`'s own verdict is `human`. Gate `commit` declares no grade and no reservation, so its own verdict is `auto`; its effective verdict is the join of the two, `human`, and the master withholds.](figures/fig1-order.svg)

### 4.4 Release and record

The master releases a terminal gate's action if and only if its effective verdict is `auto` and every egress obligation is attached; every other verdict, and ⊥, withholds [LG, SPEC §7.3]. A declared obligation is attached by its declaration; its discharge is outside the language. The master decides each terminal gate independently, so an activation that reaches two terminal gates may be released at one and withheld at the other [LG, SPEC §7.3]. Every activated gate produces one log entry, in evaluation order, carrying its effective verdict together with the declared token and the host-observed facts from which its `kind` and `risk` were derived, so that a later re-examination sees both the claim and the observation [LG, SPEC §7.4]. Evaluation is a deterministic function of the token, the host-observed facts from which its `kind` and `risk` are derived, the risk table and the policy, declaration order included. Repeated runs yield identical observations; a reordering of the declarations leaves every verdict and every master decision unchanged, and changes the log only where the tie-break of §4.3 then chooses differently [LG, SPEC §7.5].

### 4.5 What the language leaves to the host

The specification excludes execution, scheduling, storage and communication from the language [LG, SPEC §10]. It still decides release, because release is a verdict, not an act. Two places sit close to that boundary. Risk is *computed* by the gate from a governed, versioned, signed table whose content is policy [LG, SPEC §4], so some computation is inside the language. A temporal reservation declares a duration and a resolution on elapse; measuring the interval and acting on the resolution are the host's [LG, SPEC §6; `conformance/README.md`]. Neither changes the release rule: within the specification only `auto` releases, and any later activation is evaluated afresh, with no carry-over from the one that withheld [LG, SPEC §7.3]. The authenticity of `party` and the integrity of `tags` are likewise the host's [LG, SPEC §4, §10].

This is how a withheld action proceeds. In the example of §1, the high-risk `automated_decision` at `decide` is reserved for the legal role; the master withholds, and the log records the token, the observed facts and `reserved`. Nothing in the language then approves it, because a reservation reads the kind and not the actor: the same token proposed by `alice` would be reserved as well, given a grant that authorises her at that gate, and `refused` without one. The action is the role's to take, outside the language, and the record is what the role takes it on. Where the withholding is `human` — a grade too low at a graded gate — an actor holding the required grade may propose the token again, and it is evaluated from the start against its own facts. In both cases the specification draws no edge from the withholding to a later activation and forbids a reader to assume one: *“A reader MUST NOT assume the reserved action's constraints bind the follow-on activation”*; any such binding is policy [LG, SPEC §7.3]. A `redress` declaration can name a later re-examination as owed without adding that edge. The language has no transition that turns a withheld decision into a release within the same activation; it withholds, records, and evaluates the next proposal afresh. An approval that carried state across activations would be a workflow, and workflows are the host's.

<!--SECTION method-->
## 5. Method

### 5.1 One semantics in several representations

The semantics is stated in several representations (Table 2). The project's rule is that a feature counts as complete only when *“the spec, the grammar, the schemas, the vocabulary, `llms.txt`, and a conformance vector agree”* [LG, CONTRIBUTING.md]. A test enforces part of that rule in continuous integration: every declaration, every projected schema field and every grammar keyword must be exercised by at least one conformance vector [LG, `tests/lockstep_meta_test.py`]. It checks coverage, not that the representations say the same thing. Where they must agree, they do: the guard domain has the same six fields in every section of the prose, in the grammar, in the vocabulary and in the five vectors that use `reversibility` or `uncertainty`, and the prose, the syntax and the language card carry the manifest's version.

| Representation | Artefact | Count |
| --- | --- | --- |
| Normative prose | `spec/SPEC.md`, which governs on conflict | 12 sections |
| Concrete syntax | `spec/SYNTAX.md` | — |
| Grammar | `grammar/loomground.ebnf`, `grammar/tree-sitter/` | 2 |
| Data schemas | token, patch, observation, transport | 4 |
| Vocabularies | verdicts, grades, risk, cords, guard domain, rejection reasons and others | 12 |
| Agent surface | `language-card.json`, `llms.txt`, `AGENTS.md` | 3 |
| Test oracle | `conformance/manifest.json` and vectors | 75 |

Table: Table 2. Representations of the semantics, at specification version 0.11.2 (commit `081f1cf`).

### 5.2 The conformance suite

The manifest lists 75 vectors of four kinds (Table 3).

| Kind | Count | What the vector fixes | What the runner compares |
| --- | --- | --- | --- |
| patch | 40, of which 27 carry a run | the input and the projection a conforming implementation must produce; with a run, the verdict at each gate, the master decision and the ordered log | the whole observation, so an extra, missing or misordered member fails it |
| negative | 31: 27 at apply, 4 at parse | the stage at which the input is rejected, and the reason, one of twenty codes in `vocabulary/reject-reasons.json` | the stage and the reason |
| token | 2 | whether a token is well-formed or defective | the classification |
| determinism | 2 | a repeated run, and runs against reorderings of the declarations, each with the log its order fixes | verdicts and decisions unchanged; each log as its order fixes |

Table: Table 3. The conformance suite at specification version 0.11.2.

Patch vectors cover release, reservation, multi-hop propagation, fan-out and fan-in, authority at piped gates, invalid tokens inside a run, information-flow guards, prohibition, grades, quorum, temporal reservation, delegation chains, mandates and egress obligations. They also compose situations that no single declaration exercises: a fan-out and fan-in that admits two evaluation orders, declared once in each order; a prohibition combined with a high grade and a reservation on the same kind; and a token whose declared risk differs from the risk the gate computes, so that the log entry must carry both.

The conformance README binds every runner to four rules [LG, `conformance/README.md`]. A runner checks the reason for a rejection as well as its stage. It treats an exception raised while parsing as a correct rejection only for a vector declared to fail at parse. It compares the whole observation, so an extra, missing or misordered member anywhere fails the vector. And it executes the determinism vectors: repeats must agree with the expected verdicts, decisions and log, and each reordering must agree with the same verdicts and decisions and with its own log. A run may mark a token as deliberately invalid; it then contributes no expected entry and no log entry, and *“a runner MUST fail the vector if a token so marked in fact validates”* [LG, `conformance/README.md`]. A projected quorum or duration is evidence that the declaration is read correctly, not that distinct approvals are authenticated or that a timer fires.

### 5.3 Two evaluators

`loomground-ref` is a stdlib-only evaluator labelled as implementing specification 0.11.2 [REF, README.md]. `loomground-solver` evaluates the language as one component of a larger reasoning service [SOLVER]. I wrote both, in the same project, with the same agents. `loomground-ref` says so in its README and states the specification's independence criterion as open; neither repository claims independence from the other [REF, README.md; SOLVER, `docs/contracts/loomground-compatibility.md`]. The two evaluators share one structure: reachability over pipes, a memoised join over activated predecessors, and a topological order with ties broken by declaration order, the rule SPEC §7.4 makes normative. Their agreement is therefore evidence of *differential testing*, not of independent interoperability.

### 5.4 Differential testing

The same input is given to both evaluators, and their observations are compared with each other and with what the specification requires (Figure 2). Agreement reproduces a case; disagreement is a finding, resolved in the specification, the vector or an evaluator. Beyond the 75 vectors, I wrote probes aimed at priority and precedence, and at delegation bounds. For each probe, the comparison script checks the two evaluators against each other on the stage at which the policy is accepted or rejected and, for a run, on each gate's verdict, the master decision and the sequence of logged verdicts. Agreement with the specification is my reading of each case against the cited sections.

![Figure 2. Differential testing. The same input goes to both evaluators, and their observations (verdict per gate, master decision, ordered log) are compared with each other and with the specification. A disagreement is a finding, resolved in the specification, the vector or an evaluator.](figures/fig2-method.svg)

All runs use loomground at specification version 0.11.2 (tag `v0.11.2`, `081f1cf`), loomground-governance release 0.12.0 (`648cb89`), loomground-ref `2417fee` (the mutant battery of §6.3 at `0bd1e7e`), loomground-solver `fc7f0f4` and loomground-deontic release 0.2.1 (`319e218`) [DEONTIC], on 2026-10-10; the mutant battery of §6.3 ran on 2026-10-20 against the same standard. The standard in loomground-governance is pinned to loomground v0.11.2, and its copy of the vectors is byte-identical to loomground's [GOV, CHANGELOG.md, `standard/CANONICAL`]. The solver declares loomground-governance 0.12.0 as a dependency, so its own conformance gate runs the released kit and meets the full suite of 75 vectors [SOLVER, `pyproject.toml`]. Commands and raw output ship with the paper in its kit [KIT].

<!--SECTION results-->
## 6. Results

### 6.1 Replication

Both evaluators reproduce the full suite. `loomground-ref` passes 75 of 75 vectors against both copies of the standard, and 49 of 49 machine-readable checks, including a check that every non-rejecting input is accepted by its own parser. `loomground-solver` passes 75 of 75 through the conformance kit shipped with loomground-governance [GOV], and 75 of 75 through `loomground-ref`'s runner, which it meets through an adapter that translates calls and holds no language logic. The kit's bundled engine also passes 75 of 75.

The runners reject evaluators that pass by accident. Through the kit, a stub that raises on every input scores 0 of 75, and so does one that rejects every patch at apply. `loomground-ref` ships nine stubs, each breaking one rule of its runner: two reject every input, one by raising and one at the apply check; one gives a wrong reason at the right stage; two add or drop an observation key; one flips its log order between calls; one reports an undeclared gate; and two move a parse-stage rejection to the wrong place. They score between 5 and 71 of 75, every one below the total [REF, `tests/test_stub_rejection.py`].

### 6.2 Agreement beyond the suite

Eleven probes test precedence and delegation beyond the vectors. Both evaluators agree on all eleven, and in each case the outcome is the one the specification requires (Table 4). One of them, H3a, also has a counterpart in the suite, `prohibit-grade-reservation-precedence`.

| Probe | Specification requires | Both evaluators |
| --- | --- | --- |
| H1, H1′, H1″ | a high-risk automated decision under a reservation is `reserved`, including a low-risk token raised by the gate's floor and an L6 actor at an L2 gate | `reserved`, withhold |
| H3a | a prohibition beats a grant, a high grade and a reservation | `prohibited`, withhold |
| H3b, H3b′ | an ungranted actor is `refused`; two activations at one gate are both logged in order | `refused`; log `reserved`, `refused` |
| H2a–H2c | delegation that amplifies grade or risk, or forms an `on-behalf-of` cycle, is rejected at apply | rejected at apply |
| H2d | delegation that attenuates grade is accepted | accepted |
| H3c | a cord from an actor directly to the master is rejected at apply | rejected at apply |

Table: Table 4. Probes on which both evaluators agree with the specification.

### 6.3 Mutants

The stubs of §6.1 break rules the runners check; none of them gets a verdict wrong. A second battery does. Each of sixteen mutants changes one rule of the passing evaluator — a step of the priority order, the join, the release rule, a guard, the narrowing of a grant, the risk floor, the tie-break, the handling of an invalid token, and four delegation bounds — and is scored through the same runner (Table 5). Fifteen score below the total, and the vectors that fail each are named, so the suite's sensitivity to each alteration is a count rather than a claim. The counts are small: five mutants are caught by a single vector and five more by two, so where the suite reaches a rule it does so with little redundancy, and for five mutants the loss of one vector would leave them uncaught. A caught mutant shows sensitivity to that alteration, not coverage of every violation of the rule it breaks. One mutant survives. No vector runs a token above the threshold of a `risk >=` guard, so an evaluator that reads `>=` as `=` passes all 75. The gap is recorded in the test together with the vector that closes it, `guard-risk-above-threshold`, released in loomground 0.11.4 after this evaluation; the record holds only while that vector is absent, and against 0.11.4 the mutant is caught by that one vector [REF, `tests/test_semantic_mutants.py`].

| Mutant | Rule it breaks | Score | Caught by |
| --- | --- | --- | --- |
| `reserved-before-refused` | priority step 2 before 3 | 74 of 75 | `refused-precedence` |
| `refused-before-prohibited` | priority step 1 before 2 | 74 of 75 | `refused-precedence` |
| `grade-clears-reservation` | reservation independent of the actor | 73 of 75 | `grade-reserved-precedence`, `reserve-grant-independence` |
| `ungraded-actor-auto` | ungraded actor fails closed | 74 of 75 | `grade-ungraded-at-graded` |
| `no-authority-downstream` | authority checked at every gate | 71 of 75 | `pipe-authority-downstream`, `topo-fanout-fanin-declared-order`, `topo-fanout-fanin-declared-order-variant` and 1 more |
| `risk-floor-ignored` | gate floor raises the effective risk | 74 of 75 | `record-declared-and-observed` |
| `guard-ge-as-eq` | `>=` guard on an ordered property | 75 of 75 | none |
| `grant-risk-unnarrowed` | grant narrowed to risk levels | 73 of 75 | `grant-narrowing`, `reject-delegation-risk-amplify` |
| `join-least-restrictive` | join is the maximum on the chain | 70 of 75 | `grade-join`, `pipe-authority-downstream`, `topo-fanout-fanin-declared-order` and 2 more |
| `release-on-human` | only `auto` releases | 72 of 75 | `grade-human`, `grade-ungraded-at-graded`, `grade-join` |
| `log-by-name` | tie-break by declaration order | 68 of 75 | `draft-decide-run`, `grade-join`, `guard-reversibility` and 4 more |
| `invalid-token-evaluated` | invalid token denotes ⊥ | 71 of 75 | `token-validation`, `risk-enum-values`, `transport-invalid-token` and 1 more |
| `grade-amplification-allowed` | no-amplification over grade | 73 of 75 | `reject-delegation-grade-amplify`, `reject-delegation-grade-from-nothing` |
| `risk-amplification-allowed` | no-amplification over granted risk | 73 of 75 | `reject-delegation-risk-amplify`, `reject-delegation-ungranted-delegator` |
| `mandate-widening-allowed` | mandate attenuation along delegation | 73 of 75 | `reject-mandate-widen`, `reject-mandate-from-nothing` |
| `obo-cycle-allowed` | acyclic on-behalf-of | 74 of 75 | `reject-obo-cycle` |

Table: Table 5. Sixteen mutants of the passing evaluator, each breaking one rule of the semantics, scored through the strict runner at specification version 0.11.2.

<!--SECTION discussion-->
## 7. Discussion

### 7.1 What 75 of 75 establishes

An evaluator that passes the suite agrees with the specification on the inputs the vectors contain, under the rules its runners apply; it is not thereby shown correct on inputs outside them. Table 6 sets each claim the language makes against the vectors that exercise it.

| Claim | Evidence in the suite | Status |
| --- | --- | --- |
| Reservations are actor-independent | `reserve-grant-independence`, `grade-reserved-precedence` | exercised |
| Missing authority fails closed | `refused-precedence`, `grant-narrowing` at source gates; `pipe-authority-downstream` at a piped gate | exercised |
| Invalid inputs fail closed | `token-validation`; `transport-invalid-token` and `transport-invalid-token-only` inside a run | exercised |
| Delegation is bounded | 10 negative and 6 positive vectors with a delegation binding, and 3 negative transfer vectors; runners check the stage and the reason of each rejection | exercised |
| Restrictions compose | single-hop pipes; `pipe-fanout`, with fan-out, fan-in and a two-hop path; `topo-fanout-fanin-declared-order`, where a fan-in gate joins `refused` from one of two incomparable predecessors | exercised |
| Prohibitions override authority | `prohibit-tags`, `refused-precedence`; `prohibit-grade-reservation-precedence`, which combines a prohibition with a maximal grade and a same-kind reservation | exercised |
| Evaluation is auditable | log verdicts and order in every run; `record-declared-and-observed`, whose log entry carries the declared token and the observed facts | exercised |
| The record is tamper-evident | none: the specification requires tamper-evidence and leaves the mechanism to the host [LG, SPEC §7.4] | outside the specification |
| A reservation withholds release without a workflow engine | `reserved` withholds at the master | exercised |
| Quorum and temporal reservations are enforced | quorum and duration project as declared, which shows the declaration is read; authenticating parties and measuring elapse are the host's [LG, SPEC §10] | not tested |
| Verdicts and release decisions are order-independent | `topo-fanout-fanin-declared-order` and its variant, which declare two incomparable gates in opposite orders; `determinism-topo-tie`, a three-way tie under three reorderings; verdicts and decisions agree, and each log follows SPEC §7.4 | exercised |
| Decisions are deterministic | `determinism-repeat-permute`, `determinism-topo-tie`: repeated runs, and runs against reordered declarations | exercised |
| A `>=` guard on risk is read as an order | `guard-risk-ordering` projects the guard; no run places a token above its threshold, and the mutant that reads `>=` as `=` passes every vector (§6.3) | not tested |

Table: Table 6. Each claim the language makes, the evidence the suite provides, and what it does not reach.

Ten of the thirteen claims are exercised, because the suite composes the situations they depend on. Its vectors put invalid tokens inside a run, leave the actor ungranted at a piped gate, give gates two successors and two predecessors, admit two evaluation orders and fix the log for each, and combine a prohibition with a high grade and a same-kind reservation.

Three are not, and the table says which. A quorum or a duration projects as declared: that shows the declaration is read, not that distinct approvals were authenticated or that a timer fired, and no vector reaches either. The specification requires tamper-evidence but leaves its mechanism to the host, so there is nothing for a vector to check. Those two sit with the host, and a reader who needs them needs the host's evidence rather than this suite's. The third is the suite's own, found by the mutants of §6.3: the `>=` guard on risk is run only at its threshold at 0.11.2; the vector that closes the gap is in loomground 0.11.4.

The runners make the count mean what it says (§5.2, §6.1), and the mutants of §6.3 say which alterations the vectors catch and which one they do not.

### 7.2 Specified properties and consistency checks

At the points checked, the normative text agrees with itself and with its surroundings: the guard domain carries the same six fields in the prose, the grammar, the vocabulary and the vectors that use it, and the prose, the syntax and the language card carry the manifest's version (§5.1). The continuous-integration test holds coverage, not agreement, so what is stated here is a reading of those points and not a proof over the whole text. The conformance README states that the repository carries the language and no implementation of its own, and that any implementation shows conformance in the same way, by reproducing every vector. Every rejection a negative vector pins has a code in a closed vocabulary of twenty, each documented against the section of the specification that makes the case ill-formed, so the reason for a rejection is machine-checkable [LG, `vocabulary/reject-reasons.json`].

The record and its reproducibility are fixed as well. Effective verdicts do not depend on traversal order, because the join is associative, commutative and idempotent. The log does, and SPEC §7.4 settles it with a total rule: among the gates eligible next, the one declared earliest. Two conforming implementations given the same token, the same host observations and risk table, and the same policy therefore produce the same log, gate for gate and verdict for verdict. SPEC §7.5 states three rules for determinism: a repeated run yields an identical observation; a reordering of the declarations yields the same verdicts and the same master decision; and the log under such a reordering is unchanged wherever the activated gates admit a single topological order, and is otherwise the log the tie-break fixes for the new order. The determinism vectors test all three.

### 7.3 Independence

The specification's exit criterion, aligned with the IETF and W3C processes [RFC2026; RFC6410; W3C-PROCESS], is two implementations, neither derived from the other, each passing every vector. The conformance README sharpens it: the criterion is met when *“an implementation produced without access to this project's implementations reproduces every vector”*. This is the one criterion the present evaluation cannot meet by construction: the two evaluators were written in one project, and their agreement is differential testing (§5.3). The criterion names its own test. A third party builds an implementation from the specification, syntax, schemas and vocabulary alone, with the vectors withheld until the implementation is frozen, and then runs it once against all 75.

### 7.4 Scope and limitations

Conformance is a property of an implementation, not a finding of legal compliance. Separation of duty holds only relative to an external binding of `party` to an authenticated identity, and tag guards only relative to the integrity of tag assignment. The language assumes `kind` is observed by the host and `risk` computed by the gate from a governed table; a host that lets actors declare `kind` breaks that premise. The master's `act` or `withhold` is a decision; enforcement requires a host adapter with exclusive control of the effect. Finally, the probes are mine, and a different set would probe different combinations.

<!--SECTION conclusion-->
## 8. Conclusion

Governance constraints over agent actions can be stated in a small declarative language with a precise, testable semantics: priority selection at a gate, a join across gates, a single release rule, and a record whose order the declarations fix. An executable specification with 75 vectors exercises most of the claims the language makes, including the order-independence of verdicts and the determinism of evaluation under repeated and reordered runs, and names the three it does not reach. All nine stubs that break the runners' rules and fifteen of the sixteen mutants that break the semantics score below the total, so the suite is known to fail a defective evaluator and not only to pass a conforming one. The one mutant that survives is the paper's sharpest finding about its own suite: every run against a `risk >=` guard sat at the threshold, so the suite never distinguished an ordered comparison from an equality until mutation testing exposed an evaluator that treated `>=` as equality. The 0.11.2 suite the paper evaluates does not distinguish the two readings; the vector that does is in loomground 0.11.4. Both evaluators pass every vector and agree on eleven further probes. The lesson for governance languages is methodological: a conformance suite establishes what its vectors compose and what its runners check, so both belong to the specification rather than to the implementations it tests, and a suite never tried against a defective evaluator has not been shown to do either. What remains is the specification's own exit criterion: an implementation built without access to the existing two that reproduces every vector.

<!--SECTION appendices-->
## Appendix. Reproduction

The commands need a POSIX shell, Python 3.10 or later and git. `KIT` is the directory that holds this paper and its scripts. The kit is published with the paper [KIT]; its script `reproduce.sh historical WORKDIR` clones the five repositories at the pins, builds a virtual environment and writes every output under `audit/historical/`, and the listing below is what it runs.

```
KIT=/path/to/kit
for p in loomground:081f1cf loomground-governance:648cb89 \
         loomground-ref:2417fee loomground-solver:fc7f0f4 \
         loomground-deontic:319e218; do
  r=${p%%:*}; c=${p#*:}
  git clone -q https://github.com/flxk1/$r && git -C $r checkout -q $c
  echo "$r $(git -C $r rev-parse HEAD)"
done
git -C loomground-ref worktree add -q ../loomground-ref-mutants 0bd1e7e   # the mutant battery (§6.3)
python3 -m venv .venv && . .venv/bin/activate
pip install ./loomground-governance ./loomground-deontic jsonschema

# Vector counts (Table 3, §5.2)
python3 $KIT/audit/published/count_vectors.py loomground HEAD

# Replication
(cd loomground-ref    && python3 tools/verify.py ../loomground)
(cd loomground-ref    && python3 tools/verify.py ../loomground-governance/standard)
(cd loomground-ref    && LOOMGROUND_ROOT=../loomground python3 tests/test_machine_readable.py)
(cd loomground-solver && PYTHONPATH=src python3 tools/run_loomground_conformance.py)
(cd loomground-ref    && LOOMGROUND_REF=. PYTHONPATH=../loomground-solver/src \
   python3 $KIT/audit/published/solver-ref-adapter/run_ref_verify.py ../loomground)
python3 $KIT/audit/published/kit-bundled-engine.py loomground-governance

# Probes and runner behaviour
(cd loomground-ref    && LOOMGROUND_ROOT=../loomground python3 tests/test_stub_rejection.py)
(cd loomground-ref-mutants && LOOMGROUND_ROOT=../loomground python3 tests/test_semantic_mutants.py)   # Table 5
export PYTHONPATH=loomground-ref:loomground-solver/src
python3 $KIT/run_experiments.py --series H   # Table 4
python3 $KIT/audit/kit-mock-evaluators.py    # stub scores through the kit

# Quoted spans (re-derive quote-grounding.json at the pinned commits)
python3 $KIT/ground_quotes.py loomground loomground-ref $KIT/paper.md
```

The outputs of these commands, run on 2026-10-10, ship in the kit under `audit/published/`: `vector-counts.out`, `ref-verify.out`, `ref-verify-governance.out`, `ref-machine-readable.out`, `solver-conformance.out`, `solver-ref-verify.out`, `kit-bundled-engine.out`, `ref-stub-rejection.out`, `probes.out` and `kit-mock-evaluators.out`; `ref-semantic-mutants.out`, run on 2026-10-20 at loomground-ref `0bd1e7e`, is the output of Table 5. The probe battery behind Table 4 produces the following (condensed):

```
probe  case                                ref / solver
H1     DPO reservation, risk high          reserved, withhold (both)
H1'    risk low, gate floor high           reserved, withhold (both)
H1''   L6 >= required L2                   reserved, withhold (both)
H3a    prohibit beats L6 + reservation     prohibited, withhold (both)
H3b    ungranted actor                     refused, withhold (both)
H3b'   two activations, one gate           log [reserved, refused] (both)
H2a    grade amplification L3 under L2     reject@apply (both)
H2b    risk amplification                  reject@apply (both)
H2c    on-behalf-of cycle                  reject@apply (both)
H2d    attenuation L2 under L3             accepted (both)
H3c    agent -> master                     reject@apply (both)
```

<!--SECTION references-->
## References

- [LG] Loomground specification repository, https://github.com/flxk1/loomground, specification version 0.11.2, tag `v0.11.2`, commit `081f1cf`: `spec/SPEC.md`, `spec/SYNTAX.md`, `conformance/`, `schema/`, `vocabulary/`, `vocabulary/reject-reasons.json`, `language-card.json`, `tests/lockstep_meta_test.py`, `README.md`, `CONTRIBUTING.md`.
- [GOV] loomground-governance, https://github.com/flxk1/loomground-governance, release 0.12.0, commit `648cb89`: `standard/`, `standard/CANONICAL`, the conformance kit, the bundled engine `skills/loomground/loomground.py`, `CHANGELOG.md`.
- [REF] loomground-ref, https://github.com/flxk1/loomground-ref, commit `2417fee`: `loomground.py`, `tools/verify.py`, `tests/test_machine_readable.py`, `tests/test_stub_rejection.py`, `README.md`; `tests/test_semantic_mutants.py` at commit `0bd1e7e`, `docs/provenance.md`.
- [SOLVER] loomground-solver, https://github.com/flxk1/loomground-solver, commit `fc7f0f4`: `src/loomground_solver/loomground.py`, `tools/run_loomground_conformance.py`, `pyproject.toml`, `docs/contracts/loomground-compatibility.md`.
- [DEONTIC] loomground-deontic, https://github.com/flxk1/loomground-deontic, release 0.2.1, commit `319e218`, the runtime dependency the solver's `pyproject.toml` declares.
- [2OPL] M. Dastani, N. A. M. Tinnemeier, J.-J. Ch. Meyer, "A Programming Language for Normative Multi-Agent Systems", *Handbook of Research on MAS*, 397–417, 2009, doi:10.4018/978-1-60566-256-5.ch016.
- [ABAC] V. C. Hu et al., *Guide to Attribute Based Access Control (ABAC) Definition and Considerations*, NIST SP 800-162, 2014 (updated 2019).
- [AGENTBOUND] A. Kaul, Q. Lan, P. Gupta, "Behavioral Governance for Autonomous AI Agents: The AgentBound Framework", arXiv:2606.30970v2, submitted 29 June 2026, revised 1 July 2026.
- [AGENTICREI] A. Joshi, T. Finin, K. P. Joshi, L. Kagal, "Deontic Policies for Runtime Governance of Agentic AI Systems", arXiv:2606.19464, 17 June 2026; to appear, IEEE ICWS 2026.
- [AGENTSPEC] Wang, Poskitt, Sun, "AgentSpec: Customizable Runtime Enforcement for Safe and Reliable LLM Agents", arXiv:2503.18666; accepted ICSE 2026.
- [AIP] P. Singla, *Agent Identity Protocol*, Internet-Draft draft-singla-agent-identity-protocol-00, IETF, April 2026.
- [AMELI] M. Esteva, B. Rosell, J. A. Rodríguez-Aguilar, J. Ll. Arcos, "AMELI: An Agent-Based Middleware for Electronic Institutions", *AAMAS 2004*, 236–243.
- [ARTIKIS] A. Artikis, M. Sergot, J. Pitt, "Specifying norm-governed computational societies", *ACM TOCL* 10(1), 1–42, 2009, doi:10.1145/1459010.1459011.
- [BOELLA-DEL] G. Boella, L. van der Torre, "Delegation of Power in Normative Multiagent Systems", *DEON 2006*, LNCS, 36–52, doi:10.1007/11786849_6.
- [BOELLA-PROC] G. Boella, L. van der Torre, "Substantive and procedural norms in normative multiagent systems", *Journal of Applied Logic* 6(2), 152–171, 2008, doi:10.1016/j.jal.2007.06.006.
- [BSPL] A. K. Chopra, S. H. Christie V, M. P. Singh, "An Evaluation of Communication Protocol Languages for Engineering Multiagent Systems", *JAIR* 69, 1351–1393, 2020, doi:10.1613/jair.1.12212.
- [CAPMAS] Veski, Guerraoui, Froelicher, "CAPMAS: Capability-Based Delegation of Privileges in Multi-Agent Systems", arXiv:2609.06500, Sept. 2026.
- [CEDAR] J. W. Cutler et al., "Cedar: A New Language for Expressive, Fast, Safe, and Analyzable Authorization", *Proceedings of the ACM on Programming Languages* 8 (OOPSLA1), 670–697, 2024, doi:10.1145/3649835.
- [CT] B. Laurie, A. Langley, E. Kasper, *Certificate Transparency*, RFC 6962, IETF, 2013; obsoleted by B. Laurie et al., *Certificate Transparency Version 2.0*, RFC 9162, 2021.
- [CW] D. D. Clark, D. R. Wilson, "A Comparison of Commercial and Military Computer Security Policies", *IEEE Symposium on Security and Privacy*, 1987.
- [FLUME] M. Krohn et al., "Information Flow Control for Standard OS Abstractions", *SOSP*, 2007.
- [GOVERNATORI] G. Governatori, A. Rotolo, "BIO logical agents: Norms, beliefs, intentions in defeasible logic", *AAMAS Journal* 17(1), 36–69, 2008, doi:10.1007/s10458-008-9030-4.
- [GROSSI] D. Grossi, H. Aldewereld, F. Dignum, "Ubi Lex, Ibi Poena: Designing Norm Enforcement in E-Institutions", *COIN II*, LNCS, 101–114, 2007, doi:10.1007/978-3-540-74459-7_7.
- [IBRAHIM] Ibrahim, Li, "Overlaying Governance: A Compositional Authorization Framework for Delegation and Scope in Agentic AI", arXiv:2606.03518, June 2026.
- [IEEE7007] IEEE 7007-2021, *IEEE Ontological Standard for Ethically Driven Robotics and Automation Systems*, approved 24 Sept. 2021.
- [IFC] D. E. Denning, "A Lattice Model of Secure Information Flow", *Communications of the ACM* 19(5), 236–243, 1976.
- [INSTAL] O. Cliffe, M. De Vos, J. Padget, "Answer Set Programming for Representing and Reasoning About Virtual Institutions", *CLIMA VII*, LNCS, 60–79, 2007, doi:10.1007/978-3-540-69619-3_4.
- [IOLOGIC] D. Makinson, L. van der Torre, "Input/Output Logics", *Journal of Philosophical Logic* 29(4), 383–408, 2000, doi:10.1023/A:1004748624537.
- [ISO18014-3] ISO/IEC 18014-3:2009, *... Time-stamping services — Part 3: Mechanisms producing linked tokens*, 2nd ed., 2009-12.
- [ISO22989] ISO/IEC 22989:2022, *Information technology — Artificial intelligence — Artificial intelligence concepts and terminology*, 1st ed., 2022-07, ISO/IEC JTC 1/SC 42. Defs 3.1.5, 3.1.16, 3.5.6; clause 5.13 and Table 1.
- [ISO27001] ISO/IEC 27001:2022, *Information security, cybersecurity and privacy protection — Information security management systems — Requirements*, Annex A 5.3, *Segregation of duties*.
- [ISO27002] ISO/IEC 27002:2022, *Information security, cybersecurity and privacy protection — Information security controls*, 3rd ed., clause 8.15 *Logging*.
- [ISO38507] ISO/IEC 38507:2022, *... Governance implications of the use of artificial intelligence by organizations*, 2022-04.
- [ISO42001] ISO/IEC 42001:2023, *Information technology — Artificial intelligence — Management system*, 1st ed., 2023-12. A.6.2.8 event logs; A.9.2 responsible use.
- [ISO42105] ISO/IEC FDIS 42105, *... Guidance for human oversight of AI systems*, SC 42, stage 50.20 as of 2026-10-17; extends ISO/IEC TS 8200.
- [JONES] A. J. I. Jones, M. Sergot, "A Formal Characterisation of Institutionalised Power", *Logic Journal of the IGPL* 4(3), 427–443, 1996, doi:10.1093/jigpal/4.3.427.
- [KIT] F. Krone, *Whether an action may take effect* — paper and reproduction kit, https://github.com/flxk1/thoughts, directory `whether-an-action-may-take-effect`, tag `whether-an-action-may-take-effect/v1.0.1`.
- [KAOS] A. Uszok, J. M. Bradshaw, R. Jeffers et al., "KAoS policy and domain services: toward a description-logic approach to policy representation, deconfliction, and enforcement", *POLICY 2003*, 93–96, doi:10.1109/POLICY.2003.1206963.
- [LI-COMB] N. Li, Q. Wang, W. Qardaji, E. Bertino, P. Rao, J. Lobo, D. Lin, "Access control policy combining: theory meets practice", *SACMAT '09*, 135–144, doi:10.1145/1542207.1542229.
- [LOOP] Kumar, "Loopjacking: Hijacking Human-in-the-Loop Approval", arXiv:2609.21081, Sept. 2026.
- [MYERS] A. C. Myers, B. Liskov, "A decentralized model for information flow control", *SOSP '97*, 129–142, doi:10.1145/268998.266669.
- [NIST-AI-100-1] NIST AI 100-1, *Artificial Intelligence Risk Management Framework (AI RMF 1.0)*, January 2023, doi:10.6028/NIST.AI.100-1. MANAGE 2.4, MAP 3.5, GOVERN 3.2.
- [NIST80053] NIST SP 800-53 Rev. 5, *Security and Privacy Controls for Information Systems and Organizations*, control AC-5, *Separation of Duties*, 2020.
- [NPL] J. F. Hübner, O. Boissier, R. H. Bordini, "A normative programming language for multi-agent organisations", *AMAI* 62(1–2), 27–53, 2011, doi:10.1007/s10472-011-9251-0.
- [OAP] Uchibeke, "Before the Tool Call: Deterministic Pre-Action Authorization for Autonomous AI Agents", arXiv:2603.20953, March 2026.
- [OBPE] M. Millstone, T. Akidau, J. Brüderl, M. Pekker, "If Agents Were Angels, No Governance Would Be Necessary: Out-of-Band Policy Enforcement at a Trusted Tool Boundary", arXiv:2608.27646, 27 Aug 2026.
- [OCAP] M. S. Miller, *Robust Composition: Towards a Unified Approach to Access Control and Concurrency Control*, PhD thesis, Johns Hopkins University, 2006.
- [ODRL] W3C, *ODRL Information Model 2.2*, W3C Recommendation, 15 February 2018.
- [ODRL-FS] N. Fornara, V. Rodríguez-Doncel, B. Esteves, S. Steyskal, B. W. Smith, *ODRL Formal Semantics*, W3C ODRL Community Group Draft Report, 2025.
- [OPA] Open Policy Agent, *Policy Language (Rego)*, https://www.openpolicyagent.org/docs/policy-language, accessed 2026-09-26.
- [PATHS] Kaptein, Khan, Podstavnychy, "Runtime Governance for AI Agents: Policies on Paths", arXiv:2603.16586, March 2026.
- [PBEL] G. Bruns, M. Huth, "Access control via Belnap logic: Intuitive, expressive, and analyzable policy composition", *ACM TISSEC* 14(1), Article 6, 2011, doi:10.1145/1952982.1952991.
- [PLOTKIN] G. D. Plotkin, *A Structural Approach to Operational Semantics*, Technical Report DAIMI FN-19, Aarhus University, 1981; reprinted in *Journal of Logic and Algebraic Programming* 60–61, 17–139, 2004, doi:10.1016/j.jlap.2004.05.001.
- [PONDER] N. Damianou, N. Dulay, E. Lupu, M. Sloman, "The Ponder Policy Specification Language", *POLICY 2001*, LNCS 1995, 18–38, doi:10.1007/3-540-44569-2_2.
- [PROT] J. H. Saltzer, M. D. Schroeder, "The Protection of Information in Computer Systems", *Proceedings of the IEEE* 63(9), 1975.
- [RBAC] INCITS 359-2012 (R2022), *Information technology — Role Based Access Control*; first published as ANSI/INCITS 359-2004.
- [REI] L. Kagal, T. Finin, A. Joshi, "A Policy Language for a Pervasive Computing Environment", *POLICY 2003*, 63–74, doi:10.1109/POLICY.2003.1206958.
- [RFC2026] S. Bradner, *The Internet Standards Process — Revision 3*, RFC 2026, IETF, 1996.
- [RFC2753] R. Yavatkar, D. Pendarakis, R. Guerin, *A Framework for Policy-based Admission Control*, RFC 2753, IETF, January 2000, §2.
- [RFC3161] C. Adams, P. Cain, D. Pinkas, R. Zuccherato, *Internet X.509 PKI Time-Stamp Protocol (TSP)*, RFC 3161, IETF, 2001.
- [RFC3198] A. Westerinen et al., *Terminology for Policy-Based Management*, RFC 3198, IETF, November 2001, §3.
- [RFC6410] R. Housley, D. Crocker, E. Burger, *Reducing the Standards Track to Two Maturity Levels*, RFC 6410, IETF, 2011.
- [RUMPOLE] S. Marinovic, N. Dulay, M. Sloman, "Rumpole: An Introspective Break-Glass Access Control Language", *ACM TISSEC* 17(1), Article 2, 2014, doi:10.1145/2629502.
- [SAE-J3016] SAE J3016_202104, *Taxonomy and Definitions for Terms Related to Driving Automation Systems for On-Road Motor Vehicles*, April 2021 — the source of 22989's levels 0–5.
- [SCERRI] P. Scerri, D. V. Pynadath, M. Tambe, "Towards Adjustable Autonomy for the Real World", *JAIR* 17, 171–228, 2002, doi:10.1613/jair.1037.
- [SECPAL] M. Y. Becker, C. Fournet, A. D. Gordon, "SecPAL: Design and semantics of a decentralized authorization language", *Journal of Computer Security* 18(4), 619–665, 2010, doi:10.3233/JCS-2009-0364.
- [SERGOT] M. Sergot, "A computational theory of normative positions", *ACM TOCL* 2(4), 581–622, 2001, doi:10.1145/383779.383786.
- [SOUTH] T. South, S. Marro, T. Hardjono, R. Mahari, C. D. Whitney, A. Chan, A. Pentland, "Position: AI Agents Need Authenticated Delegation", *Proc. 42nd ICML*, PMLR 267:82211–82231, 2025; arXiv:2501.09674.
- [TALLAM] Tallam, "A Five-Plane Reference Architecture for Runtime Governance of Production AI Agents", arXiv:2606.12320, June 2026.
- [TBAC] R. K. Thomas, R. S. Sandhu, "Task-Based Authorization Controls (TBAC)", *IFIP WG11.3 Database Security XI*, 1997, 166–181, doi:10.1007/978-0-387-35285-5_10.
- [TONTI] G. Tonti, J. M. Bradshaw, R. Jeffers, R. Montanari, N. Suri, A. Uszok, "Semantic Web Languages for Policy Representation and Reasoning: A Comparison of KAoS, Rei, and Ponder", *ISWC 2003*, LNCS 2870, 419–437, doi:10.1007/978-3-540-39718-2_27.
- [TRIPATHI] Tripathi, Kumar, Kumar, Gadhe, "A Policy Algebra for Trust-Preserving Agentic AI Execution", arXiv:2608.16402, Aug. 2026.
- [TS] S. Haber, W. S. Stornetta, "How to Time-Stamp a Digital Document", *Journal of Cryptology* 3(2), 99–111, 1991.
- [TS8200] ISO/IEC TS 8200:2024, *... Controllability of automated artificial intelligence systems*, 1st ed., 2024-04, SC 42.
- [VIGIL] Y. Li, Y. Chen, H. Wen et al., "VIGIL: Runtime Enforcement of Behavioral Specifications in AI Agent Skills", arXiv:2606.26524, June 2026.
- [VONWRIGHT] G. H. von Wright, "Deontic Logic", *Mind* LX(237), 1–15, 1951, doi:10.1093/mind/LX.237.1.
- [W3C-PROCESS] W3C, *W3C Process Document*, 18 August 2025, §6.3.2 Implementation Experience, https://www.w3.org/policies/process/20250818/, accessed 2026-09-26.
- [X812] ITU-T Recommendation X.812 (11/95), *Information technology — Open Systems Interconnection — Security frameworks for open systems: Access control framework*; identical to ISO/IEC 10181-3:1996. Defines the access control decision function (ADF) and access control enforcement function (AEF). https://www.itu.int/rec/T-REC-X.812-199511-I.
- [XACML] OASIS, *eXtensible Access Control Markup Language (XACML) Version 3.0 Plus Errata 01*, OASIS Standard incorporating Approved Errata, 12 July 2017 (OASIS Standard of 22 January 2013).
- [XACML-CONF] OASIS XACML Technical Committee, *XACML 3.0 conformance tests*, 397 mandatory test cases, each a policy, a request and the expected response; see the XACML TC pages.
- [YAN] Yan, "Do User-Authored Permission Policies Improve Protection Against AI Agent Overreach?", arXiv:2608.27443, Aug. 2026.
