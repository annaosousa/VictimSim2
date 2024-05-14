import csv
import random
from collections import Counter
import numpy as np


class Fuzzy:
    def __init__(self):
        self.gravidade_sets = {
            'baixo': 'baixo',
            'médio': 'médio',
            'alto': 'alto',
            'crítico': 'baixo',
            'instável': 'médio',
            'potencialmente estável': 'alto',
            'estável': 'alto'
        }

    def load_data(self, path):
        signals = []

        with open(path, 'r') as csvfile:
            csvreader = csv.reader(csvfile)
            for row in csvreader:
                qp = float(row[3])  # Pressão
                pf = float(row[4])  # Batimentos
                rf = float(row[5])  # Respiração
                lb = int(row[7])    # Grupo verdadeiro

                signals.append([qp, pf, rf, lb])

        return signals

    # Função para calcular a função de pertinência triangular
    def triangular_membership(self, x, a, b, c):
        if a <= x < b:
            return (x - a) / (b - a)
        elif b <= x < c:
            return (c - x) / (c - b)
        else:
            return 0.0

    # Função para calcular a pertinência fuzzy para cada conjunto fuzzy
    def calculate_memberships(self, x, sets):
        memberships = {}
        for name, params in sets.items():
            memberships[name] = self.triangular_membership(x, *params)
        return memberships

    # Função para calcular o grau de pertinência de cada classe de gravidade
    def calculate_gravity_memberships(self, qPA, pulso, freq_respiratoria):
        qPA_sets = {'baixo': (0, 10, 15), 'médio': (
            10, 15, 20), 'alto': (15, 20, 21)}
        pulso_sets = {'baixo': (1, 5, 10), 'médio': (
            5, 10, 14), 'alto': (10, 14, 15)}
        freq_respiratoria_sets = {
            'baixo': (-6, 0, 2), 'médio': (0, 2, 6), 'alto': (2, 6, 8)}
        gravidade_sets = {'baixo': 'baixo', 'médio': 'médio', 'alto': 'alto', 'crítico': 'baixo',
                          'instável': 'médio', 'potencialmente estável': 'alto', 'estável': 'alto'}

        qPA_memberships = self.calculate_memberships(qPA, qPA_sets)
        pulso_memberships = self.calculate_memberships(pulso, pulso_sets)
        freq_respiratoria_memberships = self.calculate_memberships(
            freq_respiratoria, freq_respiratoria_sets)

        gravity_memberships = {gravidade: 0 for gravidade in gravidade_sets}

        for gravidade, params in gravidade_sets.items():
            qPA_membership = qPA_memberships[params]
            pulso_membership = pulso_memberships[params]
            freq_respiratoria_membership = freq_respiratoria_memberships[params]

            gravity_memberships[gravidade] = max(
                qPA_membership, pulso_membership, freq_respiratoria_membership)

        return gravity_memberships

    # Função para determinar a classe de gravidade com base nos graus de pertinência calculados

    def determine_gravity_class(self, gravity_memberships):
        return max(gravity_memberships, key=gravity_memberships.get)

    def split_dataset(self, dataset, split_ratio):
        random.shuffle(dataset)
        train_size = int(len(dataset) * split_ratio)
        return dataset[:train_size], dataset[train_size:]

    # Função para treinar o modelo
    def train_model(self, data_path, test_size):
        # Carregar os dados
        data = self.load_data(data_path)

        # Dividir os dados em conjuntos de treinamento e teste
        train_set, test_set = self.split_dataset(data, 1.0 - test_size)

        # Fazer previsões e calcular as métricas
        predictions = []
        actual_labels = []

        for instance in test_set:
            qPA, pulso, freq_respiratoria, label = instance
            gravity_memberships = self.calculate_gravity_memberships(
                qPA, pulso, freq_respiratoria)
            predicted_class = self.determine_gravity_class(gravity_memberships)
            predictions.append(predicted_class)
            actual_labels.append(label)

        # Calcular métricas
        accuracy = self.accuracy_metric(actual_labels, predictions)
        report = self.classification_report_metric(actual_labels, predictions)
        conf_matrix = self.confusion_matrix_metric(actual_labels, predictions)

        # Imprimir métricas
        print("\n\n------------------------------------------------------------")
        print("GENERAL METRICS\n")
        print("Reference dataset: file_target.txt Length:", len(test_set))
        # print("Predict          :", output_file, "Length:", len(predictions))
        print("Matching rows    :", len(test_set), "\n")
        print("------------------------------------------------------------")
        print("CLASSIFICATION METRICS\n")
        print("Confusion Matrix:\n", conf_matrix[1])
        print("\nAccuracy:", accuracy)
        print("\nClassification Report:")
        for key, value in report.items():
            print("\n", key, ":", value)
        print("\n------------------------------------------------------------")

        # Salvar as previsões em um arquivo CSV, se o caminho do arquivo for fornecido
        # if output_file:
        #     self.save_predictions_to_csv(test_set, predictions, output_file)

        return accuracy, test_set, predictions

    # Função para calcular a acurácia
    def accuracy_metric(self, actual, predicted):
        correct = sum(1 for x, y in zip(actual, predicted) if x == y)
        return correct / float(len(actual)) * 100.0

    # Função para calcular a matriz de confusão
    def confusion_matrix_metric(self, actual, predicted):
        # Obter rótulos únicos do dicionário gravidade_sets
        unique = list(self.gravidade_sets.keys())
        label_to_index = {label: index for index, label in enumerate(unique)}

        matrix = np.zeros((len(unique), len(unique)), dtype=int)
        for x, y in zip(actual, predicted):
            x_label = unique[x]
            matrix[label_to_index[x_label]][label_to_index[y]] += 1
        return unique, matrix

    # Função para calcular as métricas de classificação

    def classification_report_metric(self, actual, predicted):
        unique = list(set(actual))
        report = {'precision': {}, 'recall': {}, 'f1-score': {}, 'support': {}}
        correct = Counter(actual)
        total = Counter(predicted)
        for cls in unique:
            precision = correct[cls] / \
                float(total[cls]) if total[cls] != 0 else 0
            recall = correct[cls] / float(total[cls]) if total[cls] != 0 else 0
            f1_score = 2.0 * precision * recall / \
                (precision + recall) if (precision + recall) != 0 else 0
            report['precision'][cls] = precision
            report['recall'][cls] = recall
            report['f1-score'][cls] = f1_score
            report['support'][cls] = total[cls]
        return report

    # Função para salvar as previsões em um arquivo CSV
    def save_predictions_to_csv(self, data, predictions, output_file):
        with open(output_file, 'w', newline='') as csvfile:
            fieldnames = ['id', 'x', 'y', 'grav', 'classe']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for i, (row, prediction) in enumerate(zip(data, predictions)):
                writer.writerow(
                    {'id': i, 'x': 0, 'y': 0, 'grav': 0, 'classe': prediction})
