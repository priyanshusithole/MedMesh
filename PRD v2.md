Alright, Shivansh. I've gone through the entire MedMesh PRD (Draft v3.0), including the architecture, functional requirements, database design, RAG pipeline, security considerations, risks, and roadmap.

First, my overall assessment:

MedMesh — Project assessment

Workable concept

# 8/10

My preliminary assessment of the product design, not a clinical safety or implementation certification.

You have a good foundation. The project has a clear purpose, a sensible separation between deterministic logic and generative AI, and a reasonably well-defined technical architecture.

My main concern: The PRD describes how the system should work, but it does not yet fully define how the system will establish that its medication safety checks are correct and reliable.

I don't think you need to abandon the concept, simplify it into something generic, or rewrite the entire PRD.

However, I would address several architectural and product-level shortcomings before expanding the MVP.

I also want to distinguish two things throughout our discussion:

- Product shortcomings: Things that are missing from the requirements or user experience.
- Engineering shortcomings: Things that could cause incorrect results, unreliable behaviour, or deployment problems.

Let's examine both.

# 1. What I like about MedMesh

Before discussing problems, I want to highlight what you've got right.

### A. The separation of AI and clinical logic

Keep this architecture

This is probably the strongest architectural decision in your project.

Your design is:

- Deterministic engine: identifies potential safety issues.
- RAG: retrieves relevant pharmacological information.
- Gemini: converts technical information into understandable explanations.

This is much better than asking an LLM to examine a prescription and decide whether the medications are safe.

It also makes the system easier to test. You can test the safety engine independently of Gemini.

I would preserve this principle throughout development.

### B. Graceful degradation

Your fallback mechanism is another good decision.

Suppose:

- Gemini is unavailable.
- RxNav is unavailable.
- The internet connection fails.

The application should still perform whatever checks its local data supports.

However, it must clearly tell the user which checks were completed and which were unavailable. It must never present incomplete checking as a clean bill of health.

### C. The use of RxNorm

Using standardized drug identifiers is the right direction.

A drug can have:

- A brand name.
- A generic name.
- Multiple active ingredients.
- Different strengths.
- Different dosage forms.

Comparing raw text strings is not sufficient.

Normalizing medications before checking interactions is essential.

### D. Auditability

You have already thought about tracing a clinical flag to a specific rule and data row.

I would take this further by making every result traceable to:

1. The original prescription input.
2. The extracted medication.
3. The normalized drug identity.
4. The rule that triggered the flag.
5. The version of the underlying safety dataset.

This will become particularly important when you expand your drug database.

# 2. Shortcomings I would address

I have identified eight areas worth discussing. Some are important changes to the architecture, while others are missing requirements.

## Issue 1: Medication identification needs another verification layer

High priority

Your current pipeline is:

Prescription image → Gemini OCR → RxNorm normalization → Safety engine.

There is a problem here.

Imagine that a doctor writes a medication name that is difficult to read.

Gemini extracts:

`Metformin 500 mg`

But the actual prescription says:

`Metoprolol 50 mg`

These are two very different medications.

Your system could confidently normalize the wrong medication and run every subsequent safety check against the wrong drug.

The safety engine would work correctly, but the final result would still be incorrect.

My recommendation: introduce a medication confirmation screen.

Proposed prescription workflow

Prescription upload

OCR and medication extraction

Name, strength, dosage form and instructions

Medication verification

Human confirmation

The user reviews extracted medications and corrects errors.

Metformin 500 mg

Verified

Medication B

Needs review

Medication C

Uncertain

Drug normalization and safety checks

I would also extract the following fields:

- Medication name.
- Strength.
- Dosage form.
- Route of administration.
- Frequency.
- Duration.

Do not assume that identifying the medication name alone is enough.

One important point: Gemini's OCR confidence is not the same as confidence that a medication has been identified correctly. The confirmation step should apply even when OCR reports high confidence.

## Issue 2: Your deterministic engine needs a stronger data foundation

Very high priority

This is the most important issue in my opinion.

Your current safety engine covers:

1. Duplicate ingredients.
2. Drug-drug interactions.
3. Beers Criteria.
4. Allergies.

These are good starting points, but there is a major limitation.

A deterministic engine is only as reliable as the rules and data it contains.

For example, suppose your `interactions_seed.json` contains 100 known interactions.

The engine checks a prescription containing two medications that are not present in those 100 interactions.

Does that mean the combination is safe?

Absolutely not.

It only means that your configured dataset did not identify a problem.

I would change the result terminology:

| Current result | Suggested meaning                                       |
| -------------- | ------------------------------------------------------- |
| SAFE           | No known issue found in the configured checks           |
| CAUTION        | Potential concern identified                            |
| BLOCK          | Serious concern requiring immediate professional review |
| UNVERIFIED     | Insufficient data to assess                             |

I would actually avoid displaying `SAFE` altogether.

It creates a false sense of security.

### Another improvement: rule provenance

Every interaction record should contain:

- Drug A identifier.
- Drug B identifier.
- Interaction description.
- Severity.
- Clinical recommendation.
- Source of information.
- Publication or revision date.
- Dataset version.

You should also define how conflicting sources are handled.

For example, what happens if two authoritative references assign different severity levels to the same interaction?

Your PRD currently does not define this.

### One more thing: expand the clinical checks carefully

I would consider these as future candidates:

- Drug-food interactions.
- Drug-disease contraindications.
- Dose-related warnings.
- Renal impairment considerations.
- Hepatic impairment considerations.
- Pregnancy and lactation considerations.

However, don't implement all of them immediately.

Each requires appropriate patient information and validated reference data.

## Issue 3: RxNorm and Indian drug brands

High priority

This is a particularly important consideration because you are developing the project in India.

Your PRD proposes:

`Local Indian cache → NIH RxNav → Gemini fallback`

I like the architecture, but I would change the responsibilities of these components.

RxNorm is useful for standardized medication terminology. However, you should not assume that it provides complete coverage of Indian pharmaceutical brands.

Consider a medication with:

- An Indian brand name.
- Two active ingredients.
- A particular strength.
- A specific formulation.

Your system must identify the actual ingredients, not simply return a similar-looking generic name.

My suggestion:

Build a dedicated Indian medication mapping layer.

For example:

| Brand   | Active ingredients | Strength       |
| ------- | ------------------ | -------------- |
| Brand A | Ingredient X       | 500 mg         |
| Brand B | Ingredient X + Y   | 500 mg + 10 mg |
| Brand C | Ingredient Z       | 20 mg          |

These are illustrative entries, not real product mappings.

The mapping should support multiple ingredients per brand and multiple strengths and formulations.

Also, I would not let Gemini independently decide the normalized drug identity when the lookup fails.

Instead, return `UNRESOLVED` and ask for manual confirmation.

AI can suggest possible matches, but an unverified suggestion should not enter the safety engine as an established medication identity.

## Issue 4: Patient profiles are not the same as patient records

High priority

This is a product-design issue.

Your current database has:

`profiles (id, name, age, gender, created_at)`

And your primary user is a medical student.

Consider this scenario:

A medical student logs in and uploads a prescription belonging to a 70-year-old patient.

Whose age and allergies should the safety engine use?

The student's profile or the patient's actual information?

Your current design does not clearly distinguish them.

I would introduce two separate concepts:

- User account: The medical student or faculty member using MedMesh.
- Patient record: The person whose prescription is being evaluated.

A patient record could contain:

- Age.
- Allergies.
- Existing medications.
- Relevant medical conditions.
- Other information required by the checks you implement.

The user account controls access to the patient record.

This also makes your future doctor-patient history feature much easier to develop.

One additional point: avoid collecting patient information that you do not actually use. For Phase 1, synthetic or properly de-identified test records would be preferable.

## Issue 5: Your RAG pipeline needs more specific retrieval

Medium-high priority

Your current retrieval query is:

`"<generic name> mechanism, contraindications, drug interactions"`

And you retrieve the top five chunks.

This is a reasonable first implementation, but I see three shortcomings.

First: generic queries.

Suppose your deterministic engine identifies an interaction between Drug A and Drug B.

Your current query may retrieve information about Drug A's mechanism rather than information about its interaction with Drug B.

I would make retrieval flag-specific.

For example:

`Drug A + Drug B + interaction + reason identified by rule`

Second: source coverage.

Goodman & Gilman is a strong pharmacology reference, but one textbook should not become your only source for every type of safety explanation.

I would investigate adding authoritative, legally accessible sources for specific categories of information.

For example:

- Official drug labels.
- Government drug information resources.
- Appropriate clinical safety references.

Third: citation verification.

A generated explanation should not simply display a chapter name because Gemini produced one.

You should store citation metadata during ingestion:

- Book or reference name.
- Edition.
- Chapter.
- Section.
- Page, where available.
- Source identifier.

Then generate citations from retrieved metadata rather than asking the LLM to invent them.

Also, your PRD specifies `vector(768)` for Gemini embeddings. The current Google Gen AI SDK supports an explicit `output_dimensionality` setting. You must configure the embedding model to produce the same dimension used by your database.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://googleapis.github.io\&sz=32)

Google APIs+1



One more consideration: obtaining a legally acquired textbook does not automatically grant permission to ingest and process it. Your proposed internal-use approach still needs a proper copyright review.

## Issue 6: Security and patient-data privacy need more detail

High priority

You have included Supabase Auth and Row Level Security (RLS). That's good, but authentication and authorization are two different things.

Consider this:

A user signs in successfully. They then send an API request directly to your backend, bypassing your frontend.

Can they access another patient's data by changing a patient ID in the request?

Your backend must independently verify:

- The user's authentication token.
- Whether the user owns or has permission to access the requested patient record.
- Whether the requested scan belongs to that patient record.

Do not depend on frontend page restrictions.

I would also add the following:

| Area                | Requirement                                            |
| ------------------- | ------------------------------------------------------ |
| Prescription images | Private storage, not public URLs                       |
| API keys            | Backend environment variables only                     |
| Patient records     | Ownership and access verification                      |
| Data retention      | Defined retention and deletion policy                  |
| Logs                | No unnecessary patient details or prescription images  |
| Gemini API          | Document what information is sent to external services |
| Database            | Test RLS policies with multiple user accounts          |

There is another point worth considering.

Your project is being developed in India. If you eventually handle real patient information, you will need to assess applicable Indian data-protection requirements, including the DPDP framework, and the requirements that apply to your particular deployment.

For now, I would keep the test environment restricted to synthetic or de-identified prescriptions.

## Issue 7: The database schema is too small for the proposed functionality

Medium-high priority

Your current schema is:

```
profiles
profile_allergies
scans
scan_results
rag_chunks
access_grants
access_log
```

This is sufficient to demonstrate a basic MVP, but it will become difficult to maintain as you add features.

For example, consider `scan_results`:

```
scan_id
drug_name
severity
reason
```

How will you represent an interaction between two medications?

How will you distinguish an allergy flag from a duplicate ingredient flag?

How will you store the source of a particular rule?

How will you record that a user corrected an OCR result?

I would eventually introduce separate entities for:

- Patients.
- Medication records.
- Active ingredients.
- Brand-to-generic mappings.
- Safety rules.
- Interaction pairs.
- Individual safety findings.
- OCR extraction and correction history.
- Reference sources and dataset versions.

You don't need to implement every table now.

But I would design the database so that adding these features does not require rebuilding everything.

## Issue 8: Some of your technical choices need revision

Engineering priority

I checked a few of your technology choices against current documentation.

There are three points I would address.

A. Gemini Python SDK

Your PRD currently specifies:

`google-generativeai`

This is now deprecated. Google recommends the newer `google-genai` SDK, and the old SDK reached the end of support on November 30, 2025.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com\&sz=32)

GitHub+1



I would change this before expanding your Gemini integration.

B. Vercel serverless deployment

Your FastAPI + Vercel architecture is workable.

Vercel supports FastAPI through its Python runtime. However, your FastAPI application runs as a Vercel Function, so you must consider execution duration, cold starts, request size, and resource limits.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://vercel.com\&sz=32)

Vercel+1



This matters because your prescription pipeline may involve:

1. Image upload.
2. Gemini OCR.
3. Drug normalization.
4. Multiple safety checks.
5. Embedding generation.
6. Vector retrieval.
7. Gemini explanation.

These are several dependent operations.

I would avoid making the entire pipeline one large, synchronous operation without measuring its performance.

C. Your performance requirements

Your PRD specifies:

- Safety engine: under 500 ms.
- RAG: under 1.5 seconds.

I would not make these fixed acceptance requirements yet.

The safety engine's 500 ms target is reasonable to test.

But the RAG pipeline depends on external API calls, database queries, and model generation. A 1.5-second guarantee may be unrealistic.

Instead, measure:

- Average response time.
- 95th percentile response time (p95).
- OCR processing time.
- Normalization time.
- Safety engine time.
- RAG retrieval time.
- Explanation generation time.

Then establish targets based on actual measurements.

# 3. Some smaller improvements that could make a big difference

These are not necessarily architectural problems, but I would add them to our future development discussions.

| Area                | My suggestion                                                                                                                            |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Medication history  | Compare new prescriptions against existing patient medications, not just other drugs in the uploaded image                               |
| Combination drugs   | Detect duplicate ingredients even when they appear under different brand names                                                           |
| Allergy checking    | Distinguish known cross-reactivity from simple drug-class similarity                                                                     |
| Beers Criteria      | Store the edition/version and specify which recommendations are implemented                                                              |
| Dose scheduling     | Define the purpose of `scheduler.py`, which currently appears in your project structure but has no corresponding functional requirements |
| Error handling      | Define what happens when OCR, normalization, RAG or the database fails independently                                                     |
| Explainability      | Show the actual rule and reason behind each flag                                                                                         |
| Testing             | Build a collection of known positive, negative and uncertain test cases                                                                  |
| Dataset maintenance | Create a process to add, review and update medication information                                                                        |
| Accessibility       | Use text and icons alongside severity colours                                                                                            |

One particular improvement deserves attention.

### Build a proper testing framework

I would make this a core part of MedMesh rather than something you do at the end.

Create a test collection containing:

- Known duplicate ingredients.
- Known drug interactions.
- Known allergy matches.
- Beers Criteria examples.
- Unknown medication names.
- Combination drugs.
- Incorrectly extracted medication names.
- Medications absent from the local database.

For each case, define the expected outcome.

You can then run the same collection whenever you modify the safety engine.

This will help prevent a new feature from accidentally breaking an existing safety check.

# 4. A few inconsistencies inside the PRD itself

These are smaller, but worth correcting when we eventually revise the document.

| PRD section         | Observation                                                                                                                     |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| Executive Summary   | Mentions patient-specific allergies, but the data model does not clearly distinguish patients from user accounts                |
| Goals               | Mentions a future shared doctor-patient history system, but Phase 2 needs a more explicit ownership and consent model           |
| Project Structure   | Includes `scheduler.py`, but no corresponding scheduling requirements                                                           |
| Drug Normalization  | Gemini fallback can return an unverified identity                                                                               |
| Safety Engine       | `SAFE` is not a defensible conclusion when the dataset is incomplete                                                            |
| RAG                 | The retrieval process does not specify how to verify citations or define retrieval confidence                                   |
| NFR-1               | Offline operation conflicts with cloud authentication, OCR and RAG dependencies unless offline capabilities are clearly limited |
| NFR-5               | Free-tier availability and limits should be treated as external dependencies, not permanent guarantees                          |
| Acceptance Criteria | Tests whether features work, but not whether they produce correct results across a representative test collection               |

One more subtle issue: your Phase 1 acceptance criteria say that every flag should have a plain-English explanation and, where available, a Goodman & Gilman citation.

I would separate these requirements.

A flag must always have a clear explanation of the rule that triggered it. A textbook citation is additional supporting evidence, not a substitute for the underlying safety rule.

# 5. How I would divide the project into development stages

I don't want us to start adding features randomly.

I would develop MedMesh in a sequence where each stage produces a working, testable improvement to the application.

Here is my proposed roadmap. This is a development plan for discussion, not a replacement PRD.

## Proposed MedMesh development roadmap

1. Stage 0 — MVP audit

   Start here
   - Examine the existing codebase.
   - Identify implemented features.
   - Identify incomplete features and bugs.
   - Establish a baseline of existing functionality.
   Deliverable: A clear list of what works, what needs fixing, and what is missing.
2. Stage 1 — Medication data foundation
   - Improve Indian brand-to-generic mapping.
   - Handle combination drugs.
   - Introduce standardized medication identities.
   - Add data provenance and versioning.
   - Handle unresolved medications safely.
   Deliverable: A reliable medication normalization layer.
3. Stage 2 — Patient and account management
   - Separate users from patient records.
   - Implement patient-specific allergies.
   - Store existing medications.
   - Strengthen authentication and authorization.
   - Implement data access and deletion controls.
   Deliverable: A proper patient data foundation.
4. Stage 3 — Prescription intelligence
   - Improve OCR extraction.
   - Extract medication details.
   - Introduce medication verification.
   - Add manual correction.
   - Handle uncertain OCR results.
   Deliverable: A reliable prescription-to-medication pipeline.
5. Stage 4 — Safety engine enhancement
   - Improve duplicate detection.
   - Expand interaction rules.
   - Improve allergy checking.
   - Improve Beers Criteria checks.
   - Introduce `UNVERIFIED` results.
   - Build automated safety tests.
   Deliverable: A more comprehensive and testable deterministic engine.
6. Stage 5 — RAG integration
   - Build the ingestion pipeline.
   - Improve chunking and metadata.
   - Configure embedding dimensions.
   - Implement flag-specific retrieval.
   - Validate citations.
   - Implement reliable fallback explanations.
   Deliverable: Grounded, traceable explanations.
7. Stage 6 — User experience and reliability
   - Improve results presentation.
   - Add detailed explanations.
   - Add scan history.
   - Improve error handling.
   - Measure performance.
   - Test graceful degradation.
   Deliverable: A polished and reliable Phase 1 application.
8. Stage 7 — Evaluation and controlled pilot
   - Test with synthetic prescriptions.
   - Evaluate OCR accuracy.
   - Evaluate normalization accuracy.
   - Measure safety-engine performance.
   - Evaluate RAG citation accuracy.
   - Document limitations.
   Deliverable: An evaluated educational prototype ready for faculty demonstration.

I would keep your doctor-patient history, QR sharing and PDF exports outside this initial development sequence. They can follow once the core system has been properly evaluated.

# 6. My overall recommendations

If I had to select only five improvements to prioritise, they would be:

| Priority | Improvement                        | Reason                                                                             |
| -------- | ---------------------------------- | ---------------------------------------------------------------------------------- |
| 1        | Reliable medication identification | Incorrect drug identification compromises every subsequent check                   |
| 2        | Better safety datasets             | The engine cannot identify rules that it does not know                             |
| 3        | Separate patient records           | Essential for correct patient-specific checks                                      |
| 4        | Human verification                 | Prevents uncertain OCR and normalization results from silently entering the engine |
| 5        | Automated testing                  | Helps establish whether the system actually works as intended                      |

I would also migrate to `google-genai` before building more Gemini-dependent functionality.

# 7. Before we start implementing, I want to discuss three things

I don't want to assume that everything in your PRD is still pending. You mentioned that you already have a working MVP, so we should build on that rather than unnecessarily rewrite working components.

There are three decisions I think we should settle.

First: What does your current MVP actually do?

Does it already support prescription uploads, OCR, drug normalization, interaction checking and results display? Or are some of these still under development?

Second: What is the primary identity of MedMesh?

I see two possible directions:

- A. A prescription safety checker primarily designed for medical students and educational demonstrations.
- B. A medication management and safety platform that starts with medical students but is designed to evolve into a doctor-patient system.

My preference is B as the long-term architecture, while keeping A as the immediate product scope.

Third: How extensive do you want the initial safety engine to be?

I recommend starting with a smaller, well-tested collection of safety rules rather than trying to support hundreds of drugs and interactions immediately.

## Where I want us to go from here

My proposed approach is:

1. Discuss the existing MVP and settle the product direction.
2. Finalise the shortcomings we actually want to address.
3. Divide the work into detailed implementation stages.
4. Work on one stage at a time.
5. Test each stage before moving to the next.
6. Update the PRD only after we agree on the changes.

One principle I want to maintain throughout this project: Don't break a working feature just to introduce a better architecture. Improve it incrementally.

I think MedMesh has the potential to become a very good engineering project, particularly because it combines NLP, RAG, databases, backend engineering and deterministic rule-based systems.

Let's build it properly.

PRD v1.md