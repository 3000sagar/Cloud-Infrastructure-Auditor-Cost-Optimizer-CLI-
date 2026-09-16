"""Base interface all resource scanners implement.

Not yet implemented (Week 2). Each concrete scanner (EC2, EBS,
Elastic IP) will subclass this and return a list of Finding objects
for the reporting layer to consume.
"""


class BaseScanner:
    def scan(self, ctx):
        raise NotImplementedError("Scanners land in Week 2.")