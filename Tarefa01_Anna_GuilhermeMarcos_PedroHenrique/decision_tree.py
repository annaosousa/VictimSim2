import csv
import random
from collections import Counter
import numpy as np


class DecisionTree:
    def __init__(self):
        self.tree = None

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

    def split_dataset(self, dataset, split_ratio):
        random.shuffle(dataset)
        train_size = int(len(dataset) * split_ratio)
        return dataset[:train_size], dataset[train_size:]

    def gini_index(self, groups, classes):
        n_instances = float(sum(len(group) for group in groups))
        gini = 0.0
        for group in groups:
            size = float(len(group))
            if size == 0:
                continue
            score = 0.0
            for class_val in classes:
                p = [row[-1] for row in group].count(class_val) / size
                score += p * p
            gini += (1.0 - score) * (size / n_instances)
        return gini

    def get_split(self, dataset):
        class_values = list(set(row[-1] for row in dataset))
        b_index, b_value, b_score, b_groups = float(
            'inf'), float('inf'), float('inf'), None
        for index in range(len(dataset[0])-1):
            for row in dataset:
                groups = self.test_split(index, row[index], dataset)
                gini = self.gini_index(groups, class_values)
                if gini < b_score:
                    b_index, b_value, b_score, b_groups = index, row[index], gini, groups
        return {'index': b_index, 'value': b_value, 'groups': b_groups}

    def test_split(self, index, value, dataset):
        left, right = [], []
        for row in dataset:
            if row[index] < value:
                left.append(row)
            else:
                right.append(row)
        return left, right

    def to_terminal(self, group):
        outcomes = [row[-1] for row in group]
        return max(set(outcomes), key=outcomes.count)

    def split(self, node, max_depth, min_size, depth):
        left, right = node['groups']
        del node['groups']
        if not left or not right:
            node['left'] = node['right'] = self.to_terminal(left + right)
            return
        if depth >= max_depth:
            node['left'], node['right'] = self.to_terminal(
                left), self.to_terminal(right)
            return
        if len(left) <= min_size:
            node['left'] = self.to_terminal(left)
        else:
            node['left'] = self.get_split(left)
            self.split(node['left'], max_depth, min_size, depth+1)
        if len(right) <= min_size:
            node['right'] = self.to_terminal(right)
        else:
            node['right'] = self.get_split(right)
            self.split(node['right'], max_depth, min_size, depth+1)

    def build_tree(self, train, max_depth, min_size):
        root = self.get_split(train)
        self.split(root, max_depth, min_size, 1)
        return root

    def predict(self, node, row):
        if row[node['index']] < node['value']:
            if isinstance(node['left'], dict):
                return self.predict(node['left'], row)
            else:
                return node['left']
        else:
            if isinstance(node['right'], dict):
                return self.predict(node['right'], row)
            else:
                return node['right']

    def train_model(self, data_path, test_size, max_depth=19, min_size=7):
        # Carregar os dados
        data = self.load_data(data_path)

        # Dividir os dados em conjuntos de treinamento e teste
        train_set, test_set = self.split_dataset(data, 1.0 - test_size)

        # Construir a árvore de decisão
        self.tree = self.build_tree(train_set, max_depth, min_size)

        # Fazer previsões
        predictions = [self.predict(self.tree, row) for row in test_set]

        # Avaliar o desempenho do modelo
        accuracy = self.accuracy_metric(
            [row[-1] for row in test_set], predictions)
        report = self.classification_report_metric(
            [row[-1] for row in test_set], predictions)
        conf_matrix = self.confusion_matrix_metric(
            [row[-1] for row in test_set], predictions)

        # Imprimir as métricas
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
        #     self.save_predictions_to_csv(
        #         test_set, output_file)

        return accuracy, test_set

    def accuracy_metric(self, actual, predicted):
        return sum(1 for x, y in zip(actual, predicted) if x == y) / float(len(actual)) * 100.0

    def confusion_matrix_metric(self, actual, predicted):
        unique = list(set(actual))
        matrix = np.zeros((len(unique), len(unique)), dtype=int)
        for x, y in zip(actual, predicted):
            matrix[unique.index(x)][unique.index(y)] += 1
        return unique, matrix

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

    def save_predictions_to_csv(self, data, output_file):

        with open(output_file, 'w', newline='') as csvfile:
            fieldnames = ['id', 'x', 'y', 'grav', 'classe']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for i, row in enumerate(data):
                prediction = self.predict(self.tree, row)
                writer.writerow(
                    {'id': i, 'x': 0, 'y': 0, 'grav': 0, 'classe': prediction})
