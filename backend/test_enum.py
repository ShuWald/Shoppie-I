from app.models import SuggestedAction

print('Backend enum values:')
for action in SuggestedAction:
    print(f'  - {action.name}: "{action.value}"')
