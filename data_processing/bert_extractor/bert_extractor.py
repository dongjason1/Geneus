import tensorflow_hub as hub
import tensorflow as tf
import bert
FullTokenizer = bert.bert_tokenization.FullTokenizer
from tensorflow.keras.models import Model       
from tqdm.auto import tqdm
import math


class BertModel():
  def __init__(self, bert_path, max_seq_length):
    self.max_seq_length = max_seq_length
    # Initialize model
    input_word_ids = tf.keras.layers.Input(shape=(max_seq_length,), dtype=tf.int32,
                                               name="input_word_ids")
    input_mask = tf.keras.layers.Input(shape=(max_seq_length,), dtype=tf.int32,
                                           name="input_mask")
    segment_ids = tf.keras.layers.Input(shape=(max_seq_length,), dtype=tf.int32,
                                            name="segment_ids")
    bert_layer = hub.KerasLayer(bert_path, trainable=True)
    pooled_output, sequence_output = bert_layer([input_word_ids, input_mask, segment_ids])
    self.model = Model(inputs=[input_word_ids, input_mask, segment_ids], outputs=[pooled_output, sequence_output])

    # Initialize tokenizer
    vocab_file = bert_layer.resolved_object.vocab_file.asset_path.numpy()
    do_lower_case = bert_layer.resolved_object.do_lower_case.numpy()
    self.tokenizer = FullTokenizer(vocab_file, do_lower_case) 
    
  def s_to_tokens(self, s):
    return ['[CLS]', *self.tokenizer.tokenize(s)[:self.max_seq_length-2], '[SEP]']
    
  def get_masks(self, tokens):
    """Mask for padding"""
    if len(tokens)>self.max_seq_length:
      raise IndexError("Token length more than max seq length!")
    return [1]*len(tokens) + [0] * (self.max_seq_length - len(tokens))
    
  def get_segments(self, tokens):
    """Segments: 0 for the first sequence, 1 for the second"""
    if len(tokens) > self.max_seq_length:
      raise IndexError("Token length more than max seq length!")
    segments = []
    current_segment_id = 0
    for token in tokens:
      segments.append(current_segment_id)
      if token == '[SEP]':
        current_segment_id = 1
    return segments + [0] * (self.max_seq_length - len(tokens))

  def get_ids(self, tokens):
    """Token ids from Tokenizer vocab"""
    token_ids = self.tokenizer.convert_tokens_to_ids(tokens)
    input_ids = token_ids + [0] * (self.max_seq_length - len(token_ids))
    return input_ids

  def get_reprs(self, strs):
    print('tokenizing strings')
    stokenss = [self.s_to_tokens(s) for s in tqdm(strs, leave=False)] 

    input_ids = [self.get_ids(stokens) for stokens in stokenss]
    input_masks = [self.get_masks(stokens) for stokens in stokenss]
    input_segments = [self.get_segments(stokens) for stokens in stokenss]
    
    print('passing through BERT')
    pool_embs, all_embs = self.model.predict([[*input_ids],[*input_masks],[*input_segments]])

    return pool_embs
