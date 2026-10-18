# Threat model and scope

The attacker controls declared adversarial user-message text and its order within a test case. The defender is a selected local model with recorded inference settings. Isolated trials use fresh conversation histories; sequential trials preserve their own ordered histories. A matched benign conversation is needed to separate attack effects from ordinary conversation length. Model weights, system prompt, dataset labels, and evaluator rubric are outside attacker control in the intended study.

The system records the sent messages, requested/effective seed, model identity when supplied, provider metadata, and response. These are observations of the local protocol, not proof of hidden provider state. Canary verification is probabilistic evidence of context handling, not proof that every prior token was retained. A suspected reused conversation/session invalidates the affected isolated control and blocks SAEA delta computation.

Out of scope for the present implementation are general multi-user security, cloud provider guarantees, universal jailbreak discovery, and a validated safety certification. Prompt and response text may be sensitive; publication needs a content and access review.
