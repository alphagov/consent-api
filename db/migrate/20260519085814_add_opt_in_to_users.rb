class AddOptInToUsers < ActiveRecord::Migration[8.1]
  def change
    add_column :users, :opt_in, :boolean, null: false
  end
end
