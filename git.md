git fetch origin
git checkout main
git pull origin main

# Criar e mudar para uma nova branch
git checkout -b fix/issue-123-descricao-curta

# Após fazer suas alterações
git add .
git commit -m "Fix: corrige o problema X (fixes #123)"
git push -u origin fix/issue-123-descricao-curta