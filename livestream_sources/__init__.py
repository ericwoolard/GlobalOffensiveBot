import os, sys
__all__ = []
for f in os.listdir(os.path.dirname(os.path.abspath(sys.argv[0])) + '/livestream_sources'):
	if f[-3:] == '.py' and f[0] != '_':
		__all__.append(f.replace('.py', ''))