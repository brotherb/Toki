import os

extens = [".py", ".html"]
lines_sum = 0
lines_py = 0
lines_html = 0

for root, dirs, filenames in os.walk('.'):
    for f in filenames:
        fname = os.path.join(root, f)
        if fname.endswith('.py'):
            with open(fname, 'r') as t:
                for line in t:
                    lines_py += 1
                    lines_sum += 1

        if fname.endswith('.html'):
            with open(fname, 'r') as t:
                for line in t:
                    lines_html += 1
                    lines_sum += 1

print ('sum: %d' % lines_sum)
print ('lines of html: %d' % lines_html)
print ('lines of py: %d' % lines_py)
