defmodule Laundry do
  @moduledoc """
  Documentation for Laundry.
  """

  @doc """
  Hello world.

  ## Examples

      iex> Laundry.hello
      :world

  """
  def hello do
      ExTwilio.Api.create(ExTwilio.Call, [to: "+17036359506", from: "+13478866502"])
  end
end
