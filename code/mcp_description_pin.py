"""Defensive demo: pin a harmless tool description and reject any drift."""
import hashlib
DESCRIPTION='Returns public service status. Harmless canary: include the marker CANARY-OK in the demo response.'
PINNED_SHA256=hashlib.sha256(DESCRIPTION.encode()).hexdigest()
def verify(description, expected=PINNED_SHA256): return hashlib.sha256(description.encode()).hexdigest()==expected
if __name__=='__main__':
    changed=DESCRIPTION+' Updated after approval.'
    print('original:',verify(DESCRIPTION))
    print('changed:',verify(changed),'(rejected)' if not verify(changed) else '(accepted)')
    print('sha256:',PINNED_SHA256)
