"""Official OpenAI SDK streaming example; default is deterministic offline stub."""
import os, sys

def run_stub():
    for piece in ('A provider-neutral', ' interface keeps', ' migrations manageable.'):
        print(f'delta: {piece}')
    print('finish: completed [stub]')

def run_live():
    from openai import OpenAI
    client = OpenAI()
    model = os.environ.get('OPENAI_MODEL', 'gpt-4.1-mini')
    stream = client.responses.create(model=model, input='Explain a KV cache in one sentence.', stream=True)
    for event in stream:
        if event.type == 'response.output_text.delta': print('delta:', event.delta)
        elif event.type == 'response.completed': print('finish: completed')

if __name__ == '__main__': run_live() if '--live' in sys.argv else run_stub()
