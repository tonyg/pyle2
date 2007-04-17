import Group

Anybody = Group.Public()
Logged_in_user = not Group.Anonymous()

# LShift_Email = Group.EmailDomain('lshift.net')
# CohesiveFT_Email = Group.EmailDomain('cohesiveft.com')
# Rabbit_Email = LShift_Email | CohesiveFT_Email | Group.EmailDomain('rabbitmq.com')
