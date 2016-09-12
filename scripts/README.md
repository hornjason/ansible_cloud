# Generate the dictionary:
python ./loop.py <<infra name>> <<nb chassis>> <<nv utility servers>>
# e.g.
python ./loop.py scos01 3 2 > group_vars/all

# Execute the role:
ansible-playbook --ask-pass -i hosts check-dict.yml
