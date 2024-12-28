echo "Running bandit..."
bandit -r app/ skills/ skill_sets/ utils/ -ll

echo "Running pylint..."
pylint .

echo "Running black..."
black .

echo "Running isort..."
isort .
