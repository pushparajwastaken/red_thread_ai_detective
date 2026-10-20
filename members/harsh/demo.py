"""Offline demo: python -m members.harsh.demo (from the repository root)."""
import json

from shared.contracts import DialogueDraft, DialogueRequest, NPCContext
from shared.fixture_case import make_case_001
from members.harsh.validator import validate_dialogue


def main():
    case = make_case_001()
    npc = NPCContext('gardener', ['F001', 'F002'], permitted_evidence_ids=['E001', 'E003'])
    request = DialogueRequest('gardener', 'What did you see?', ['F001', 'F002'], ['E001', 'E003'])
    scenarios = {
        'authorized': DialogueDraft('gardener', 'I saw a figure near the greenhouse.', ['F001']),
        'missing_citation': DialogueDraft('gardener', 'I saw a figure near the greenhouse.'),
        'protected_term': DialogueDraft('gardener', 'The brandy was poisoned.'),
        'timeout': DialogueDraft('gardener', status='timeout'),
    }
    for name, draft in scenarios.items():
        result = validate_dialogue(request, draft, case, npc)
        # Developer demo only. The player UI must display result.text alone.
        print(json.dumps({'scenario': name, 'text': result.text, 'valid': result.valid,
                          'used_fallback': result.used_fallback, 'reasons': result.reasons}))


if __name__ == '__main__':
    main()
