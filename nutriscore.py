import pickle
import numpy as np

CSV_INDEX_TO_RELATIONSHIP = [
    'id',
    'url',
    'title',
    'img_url',
    'servings',
    'prep_time',
    'rating',
    'reviews',
    'made_it_count',
    'calories',
    'total_fat',
    'saturated_fat',
    'cholesterol',
    'sodium',
    'potassium',
    'total_carbohydrates',
    'dietary_fiber',
    'protein',
    'sugars',
    'vitamin_a',
    'vitamin_c',
    'calcium',
    'iron',
    'thiamin',
    'niacin',
    'vitamin_b6',
    'magnesium',
    'folate',
    # Everything above this index is a <contains> relationship
]


def load_model(filename):
    with open(filename, 'rb') as f:
        model = pickle.load(f)
    return model


protein_index = CSV_INDEX_TO_RELATIONSHIP.index('protein')
fat_index = CSV_INDEX_TO_RELATIONSHIP.index('total_fat')
carb_index = CSV_INDEX_TO_RELATIONSHIP.index('total_carbohydrates')


def compute_aug_cols(data):
    protein_cals = float(data[protein_index]) * 4.0
    fat_cals = float(data[fat_index]) * 9.0
    carb_cals = float(data[carb_index]) * 4.0

    total_cals = sum([protein_cals, fat_cals, carb_cals])
    cal_protein = protein_cals / total_cals
    cal_fat = fat_cals / total_cals
    cal_carbs = carb_cals / total_cals

    return [cal_protein, cal_fat, cal_carbs]


def compute_input(recipe):
    recipe_data = recipe[6:len(CSV_INDEX_TO_RELATIONSHIP)-1]
    recipe_data = np.array(recipe_data).astype(np.float64)

    # Compute augmented features, the 1 is the bias term
    recipe_data = np.append(recipe_data, compute_aug_cols(recipe))
    recipe_data = np.append(recipe_data, 1)

    return recipe_data


def predict_nutriscore(model, recipe):
    return model.predict(compute_input(recipe).reshape(1, -1))[0]
