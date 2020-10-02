import cProfile
import pstats

pr = cProfile.Profile()
pr.enable()

method_to_profile()

pr.disable()
with open(r'c:\temp\output.txt', 'w+') as f:
    ps = pstats.Stats(pr, stream=f)
    ps.strip_dirs().sort_stats(-1).print_stats()